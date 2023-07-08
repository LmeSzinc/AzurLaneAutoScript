import re
import time
from datetime import timedelta

import cv2
from ppocronnx.predict_system import BoxedResult

import module.config.server as server
from module.base.button import ButtonWrapper
from module.base.decorator import cached_property
from module.base.utils import area_pad, corner2area, crop, float2str
from module.exception import ScriptError
from module.logger import logger
from module.ocr.models import OCR_MODEL
from module.ocr.ppocr import TextSystem
from module.ocr.utils import merge_buttons


def enlarge_canvas(image):
    """
    Enlarge image into a square fill with black background. In the structure of PaddleOCR,
    image with w:h=1:1 is the best while 3:1 rectangles takes three times as long.
    Also enlarge into the integer multiple of 32 cause PaddleOCR will downscale images to 1/32.
    """
    height, width = image.shape[:2]
    length = int(max(width, height) // 32 * 32 + 32)
    border = (0, length - height, 0, length - width)
    if sum(border) > 0:
        image = cv2.copyMakeBorder(image, *border, borderType=cv2.BORDER_CONSTANT, value=(0, 0, 0))
    return image


class OcrResultButton:
    def __init__(self, boxed_result: BoxedResult, keyword_classes: list):
        """
        Args:
            boxed_result: BoxedResult from ppocr-onnx
            keyword_classes: List of Keyword classes
        """
        self.area = boxed_result.box
        self.search = area_pad(self.area, pad=-20)
        # self.color =
        self.button = boxed_result.box

        try:
            self.matched_keyword = self.match_keyword(boxed_result.ocr_text, keyword_classes)
            self.name = str(self.matched_keyword)
        except ScriptError:
            self.matched_keyword = None
            self.name = boxed_result.ocr_text

        self.text = boxed_result.ocr_text
        self.score = boxed_result.score

    @staticmethod
    def match_keyword(ocr_text, keyword_classes):
        """
        Args:
            ocr_text (str):
            keyword_classes: List of Keyword classes

        Returns:
            Keyword:

        Raises:
            ScriptError: If no keywords matched
        """
        for keyword_class in keyword_classes:
            try:
                matched = keyword_class.find(ocr_text, in_current_server=True, ignore_punctuation=True)
                return matched
            except ScriptError:
                continue

        raise ScriptError

    def __str__(self):
        return self.name

    __repr__ = __str__

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.name)

    def __bool__(self):
        return True


class Ocr:
    # Merge results with box distance <= thres
    merge_thres_x = 0
    merge_thres_y = 0

    def __init__(self, button: ButtonWrapper, lang=None, name=None):
        self.button: ButtonWrapper = button
        self._lang = lang
        self.name: str = name if name is not None else button.name

    @classmethod
    def server2lang(cls, ser=None) -> str:
        if ser is None:
            ser = server.server
        match ser:
            case 'cn':
                return 'ch'
            case _:
                return 'ch'

    @cached_property
    def lang(self) -> str:
        return self._lang if self._lang is not None else Ocr.server2lang()

    @cached_property
    def model(self) -> TextSystem:
        return OCR_MODEL.__getattribute__(self.lang)

    def pre_process(self, image):
        """
        Args:
            image (np.ndarray): Shape (height, width, channel)

        Returns:
            np.ndarray: Shape (width, height)
        """
        return image

    def after_process(self, result):
        """
        Args:
            result (str): '第二行'

        Returns:
            str:
        """
        if result.startswith('UID'):
            result = 'UID'
        return result

    def format_result(self, result):
        """
        Will be overriden.
        """
        return result

    def ocr_single_line(self, image):
        # pre process
        start_time = time.time()
        image = crop(image, self.button.area)
        image = self.pre_process(image)
        # ocr
        result, _ = self.model.ocr_single_line(image)
        # after proces
        result = self.after_process(result)
        result = self.format_result(result)
        logger.attr(name='%s %ss' % (self.name, float2str(time.time() - start_time)),
                    text=str(result))
        return result

    def ocr_multi_lines(self, image_list):
        # pre process
        start_time = time.time()
        image_list = [self.pre_process(image) for image in image_list]
        # ocr
        result_list = self.model.ocr_lines(image_list)
        result_list = [(result, score) for result, score in result_list]
        # after process
        result_list = [(self.after_process(result), score) for result, score in result_list]
        result_list = [(self.format_result(result), score) for result, score in result_list]
        logger.attr(name="%s %ss" % (self.name, float2str(time.time() - start_time)),
                    text=str([result for result, _ in result_list]))
        return result_list

    def detect_and_ocr(self, image, direct_ocr=False) -> list[BoxedResult]:
        """
        Args:
            image:
            direct_ocr: True to ignore `button` attribute and feed the image to OCR model without cropping.

        Returns:

        """
        # pre process
        start_time = time.time()
        if not direct_ocr:
            image = crop(image, self.button.area)
        image = self.pre_process(image)
        # ocr
        image = enlarge_canvas(image)
        results: list[BoxedResult] = self.model.detect_and_ocr(image)
        # after proces
        for result in results:
            if not direct_ocr:
                result.box += self.button.area[:2]
            result.box = tuple(corner2area(result.box))
        results = merge_buttons(results, thres_x=self.merge_thres_x, thres_y=self.merge_thres_y)
        for result in results:
            result.ocr_text = self.after_process(result.ocr_text)

        logger.attr(name='%s %ss' % (self.name, float2str(time.time() - start_time)),
                    text=str([result.ocr_text for result in results]))
        return results

    def matched_ocr(self, image, keyword_classes, direct_ocr=False) -> list[OcrResultButton]:
        """
        Args:
            image: Screenshot
            keyword_classes: `Keyword` class or classes inherited `Keyword`, or a list of them.
            direct_ocr: True to ignore `button` attribute and feed the image to OCR model without cropping.

        Returns:
            List of matched OcrResultButton.
            OCR result which didn't matched known keywords will be dropped.
        """
        if not isinstance(keyword_classes, list):
            keyword_classes = [keyword_classes]

        def is_valid(keyword):
            # Digits will be considered as the index of keyword
            if keyword.isdigit():
                return False
            return True

        results = self.detect_and_ocr(image, direct_ocr=direct_ocr)
        results = [
            OcrResultButton(result, keyword_classes)
            for result in results if is_valid(result.ocr_text)
        ]
        results = [result for result in results if result.matched_keyword is not None]
        logger.attr(name=f'{self.name} matched',
                    text=results)
        return results


class Digit(Ocr):
    def __init__(self, button: ButtonWrapper, lang='ch', name=None):
        super().__init__(button, lang=lang, name=name)

    def format_result(self, result) -> int:
        """
        Returns:
            int:
        """
        result = super().after_process(result)
        logger.attr(name=self.name, text=str(result))

        res = re.search(r'(\d+)', result)
        if res:
            return int(res.group(1))
        else:
            logger.warning(f'No digit found in {result}')
            return 0


class DigitCounter(Ocr):
    def __init__(self, button: ButtonWrapper, lang='ch', name=None):
        super().__init__(button, lang=lang, name=name)

    def format_result(self, result) -> tuple[int, int, int]:
        """
        Do OCR on a counter, such as `14/15`, and returns 14, 1, 15

        Returns:
            int:
        """
        result = super().after_process(result)
        logger.attr(name=self.name, text=str(result))

        res = re.search(r'(\d+)/(\d+)', result)
        if res:
            groups = [int(s) for s in res.groups()]
            current, total = int(groups[0]), int(groups[1])
            # current = min(current, total)
            return current, total - current, total
        else:
            logger.warning(f'No digit counter found in {result}')
            return 0, 0, 0


class Duration(Ocr):
    @cached_property
    def timedelta_regex(self):
        regex_str = {
            'ch': r'\D*((?P<days>\d{1,2})天)?((?P<hours>\d{1,2})小时)?((?P<minutes>\d{1,2})分钟)?((?P<seconds>\d{1,2})秒})?',
            'en': r'\D*((?P<days>\d{1,2})d\s*)?((?P<hours>\d{1,2})h\s*)?((?P<minutes>\d{1,2})m\s*)?((?P<seconds>\d{1,2})s)?'
        }[self.lang]
        return re.compile(regex_str)

    def format_result(self, result: str) -> timedelta:
        """
        Do OCR on a duration, such as `18d 2h 13m 30s`, `2h`, `13m 30s`, `9s`

        Returns:
            timedelta:
        """
        matched = self.timedelta_regex.match(result)
        if matched is None:
            return timedelta()
        days = self._sanitize_number(matched.group('days'))
        hours = self._sanitize_number(matched.group('hours'))
        minutes = self._sanitize_number(matched.group('minutes'))
        seconds = self._sanitize_number(matched.group('seconds'))
        return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    @staticmethod
    def _sanitize_number(number) -> int:
        if number is None:
            return 0
        return int(number)
