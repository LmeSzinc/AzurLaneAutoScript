import time

from ppocronnx.predict_system import BoxedResult

import module.config.server as server
from module.base.button import ButtonWrapper
from module.base.decorator import cached_property
from module.base.utils import area_pad, crop, float2str
from module.exception import ScriptError
from module.logger import logger
from module.ocr.models import OCR_MODEL
from module.ocr.ppocr import TextSystem


class OcrResultButton:
    def __init__(self, boxed_result: BoxedResult, keyword_class):
        self.area = boxed_result.box
        self.search = area_pad(self.area, pad=-20)
        # self.color =
        self.button = boxed_result.box

        try:
            self.matched_keyword = keyword_class.find(
                boxed_result.ocr_text, in_current_server=True, ignore_punctuation=True)
            self.name = f'{keyword_class.__name__}_{self.matched_keyword.id}'
        except ScriptError:
            self.matched_keyword = None
            self.name = boxed_result.ocr_text

        self.image = boxed_result.text_img
        self.text = boxed_result.ocr_text
        self.score = boxed_result.score

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
    def __init__(self, button: ButtonWrapper, lang=None, name=None):
        self.button: ButtonWrapper = button
        self.lang: str = lang if lang is not None else Ocr.server2lang()
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
        logger.attr(name='%s %ss' % (self.name, float2str(time.time() - start_time)),
                    text=str(result))
        return result

    def detect_and_ocr(self, image) -> list[BoxedResult]:
        # pre process
        start_time = time.time()
        image = crop(image, self.button.area)
        image = self.pre_process(image)
        # ocr
        results: list[BoxedResult] = self.model.detect_and_ocr(image)
        # after proces
        for result in results:
            result.ocr_text = self.after_process(result.ocr_text)
        logger.attr(name='%s %ss' % (self.name, float2str(time.time() - start_time)),
                    text=str([result.ocr_text for result in results]))
        return results

    def matched_ocr(self, image, keyword_class) -> list[OcrResultButton]:
        """
        Args:
            image: Screenshot
            keyword_class: `Keyword` class or classes inherited `Keyword`

        Returns:
            List of matched OcrResultButton.
            OCR result which didn't matched known keywords will be dropped.
        """
        results = [OcrResultButton(result, keyword_class) for result in self.detect_and_ocr(image)]
        results = [result for result in results if result.matched_keyword is not None]
        logger.attr(name=f'{self.name} matched',
                    text='[' + ', '.join([result.name for result in results]) + ']')
        return results
