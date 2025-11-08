import time
from datetime import timedelta
from typing import TYPE_CHECKING

import module.config.server as server
from module.base.button import Button
from module.base.decorator import cached_property
from module.base.utils import *
from module.logger import logger
from module.ocr.rpc import ModelProxyFactory
from module.webui.setting import State

if TYPE_CHECKING:
    from module.ocr.al_ocr import AlOcr

if not State.deploy_config.UseOcrServer:
    from module.ocr.models import OCR_MODEL
else:
    OCR_MODEL = ModelProxyFactory()


class Ocr:
    SHOW_LOG = True
    SHOW_REVISE_WARNING = False

    def __init__(self, buttons, lang='azur_lane', letter=(255, 255, 255), threshold=128, alphabet=None, name=None):
        """
        Args:
            buttons (Button, tuple, list[Button], list[tuple]): OCR area.
            lang (str): 'azur_lane' or 'cnocr'.
            letter (tuple(int)): Letter RGB.
            threshold (int):
            alphabet: Alphabet white list.
            name (str):
        """
        self.name = str(buttons) if isinstance(buttons, Button) else name
        self._buttons = buttons
        self.letter = letter
        self.threshold = threshold
        self.alphabet = alphabet
        self.lang = lang
        if lang == 'azur_lane' and server.server in ['jp']:
            self.lang = 'azur_lane_' + server.server

    @property
    def cnocr(self) -> "AlOcr":
        return OCR_MODEL.__getattribute__(self.lang)

    @property
    def buttons(self):
        buttons = self._buttons
        buttons = buttons if isinstance(buttons, list) else [buttons]
        buttons = [button.area if isinstance(button, Button) else button for button in buttons]
        return buttons

    @buttons.setter
    def buttons(self, value):
        self._buttons = value

    def pre_process(self, image):
        """
        Args:
            image (np.ndarray): Shape (height, width, channel)

        Returns:
            np.ndarray: Shape (width, height)
        """
        image = extract_letters(image, letter=self.letter, threshold=self.threshold)

        return image.astype(np.uint8)

    def after_process(self, result):
        """
        Args:
            result (str): '第二行'

        Returns:
            str:
        """
        return result

    def ocr(self, image, direct_ocr=False):
        """
        Args:
            image (np.ndarray, list[np.ndarray]):
            direct_ocr (bool): True to skip preprocess.

        Returns:

        """
        start_time = time.time()

        if direct_ocr:
            image_list = [self.pre_process(i) for i in image]
        else:
            image_list = [self.pre_process(crop(image, area)) for area in self.buttons]

        # This will show the images feed to OCR model
        # self.cnocr.debug(image_list)

        result_list = self.cnocr.atomic_ocr_for_single_lines(image_list, self.alphabet)
        result_list = [''.join(result) for result in result_list]
        result_list = [self.after_process(result) for result in result_list]

        if len(self.buttons) == 1:
            result_list = result_list[0]
        if self.SHOW_LOG:
            logger.attr(name='%s %ss' % (self.name, float2str(time.time() - start_time)),
                        text=str(result_list))

        return result_list


class OcrYuv(Ocr):
    """
    Do OCR in the Y channel of the YUV color space.
    """

    @cached_property
    def letter_y(self):
        arr = np.array([[self.letter]], dtype=np.uint8)
        y = rgb2luma(arr)[0][0]
        return y

    def pre_process(self, image):
        """
        Args:
            image (np.ndarray): Shape (height, width, channel)

        Returns:
            np.ndarray: Shape (width, height)
        """
        y = rgb2luma(image)
        letter_y = (np.ones(y.shape) * self.letter_y).astype(np.uint8)
        diff = cv2.absdiff(y, letter_y)
        diff = cv2.multiply(diff, 255.0 / self.threshold)
        return diff


class Digit(Ocr):
    """
    Do OCR on a digit, such as `45`.
    Method ocr() returns int, or a list of int.
    """

    def __init__(self, buttons, lang='azur_lane', letter=(255, 255, 255), threshold=128, alphabet='0123456789IDSB',
                 name=None):
        super().__init__(buttons, lang=lang, letter=letter, threshold=threshold, alphabet=alphabet, name=name)

    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('I', '1').replace('D', '0').replace('S', '5')
        result = result.replace('B', '8')

        prev = result
        result = int(result) if result else 0
        if self.SHOW_REVISE_WARNING:
            if str(result) != prev:
                logger.warning(f'OCR {self.name}: Result "{prev}" is revised to "{result}"')

        return result


class DigitYuv(Digit, OcrYuv):
    pass


class DigitCounter(Ocr):
    def __init__(self, buttons, lang='azur_lane', letter=(255, 255, 255), threshold=128, alphabet='0123456789/IDSB',
                 name=None):
        super().__init__(buttons, lang=lang, letter=letter, threshold=threshold, alphabet=alphabet, name=name)

    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('I', '1').replace('D', '0').replace('S', '5')
        result = result.replace('B', '8')
        return result

    def ocr(self, image, direct_ocr=False):
        """
        DigitCounter only support doing OCR on one button.
        Do OCR on a counter, such as `14/15`, and returns 14, 1, 15

        Args:
            image:
            direct_ocr:

        Returns:
            int, int, int: current, remain, total.
        """
        result_list = super().ocr(image, direct_ocr=direct_ocr)
        result = result_list[0] if isinstance(result_list, list) else result_list

        result = re.search(r'(\d+)/(\d+)', result)
        if result:
            result = [int(s) for s in result.groups()]
            current, total = int(result[0]), int(result[1])
            current = min(current, total)
            return current, total - current, total
        else:
            logger.warning(f'Unexpected ocr result: {result_list}')
            return 0, 0, 0


class DigitCounterYuv(DigitCounter, OcrYuv):
    pass


class Duration(Ocr):
    def __init__(self, buttons, lang='azur_lane', letter=(255, 255, 255), threshold=128, alphabet='0123456789:IDSB',
                 name=None):
        super().__init__(buttons, lang=lang, letter=letter, threshold=threshold, alphabet=alphabet, name=name)

    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('I', '1').replace('D', '0').replace('S', '5')
        result = result.replace('B', '8')
        return result

    def ocr(self, image, direct_ocr=False):
        """
        Do OCR on a duration, such as `01:30:00`.

        Args:
            image:
            direct_ocr:

        Returns:
            list, datetime.timedelta: timedelta object, or a list of it.
        """
        result_list = super().ocr(image, direct_ocr=direct_ocr)
        if not isinstance(result_list, list):
            result_list = [result_list]
        result_list = [self.parse_time(result) for result in result_list]
        if len(self.buttons) == 1:
            result_list = result_list[0]
        return result_list

    @staticmethod
    def parse_time(string):
        """
        Args:
            string (str): `01:30:00`

        Returns:
            datetime.timedelta:
        """
        result = re.search(r'(\d{1,2}):?(\d{2}):?(\d{2})', string)
        if result:
            result = [int(s) for s in result.groups()]
            return timedelta(hours=result[0], minutes=result[1], seconds=result[2])
        else:
            logger.warning(f'Invalid duration: {string}')
            return timedelta(hours=0, minutes=0, seconds=0)


class DurationYuv(Duration, OcrYuv):
    pass
