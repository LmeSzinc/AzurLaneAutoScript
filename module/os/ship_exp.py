import re

from module.awaken.assets import OCR_SHIP_LEVEL, OCR_SHIP_EXP
from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import Ocr, Digit


class ShipLevel(Digit):
    def after_process(self, result):
        result = super().after_process(result)
        if result < 1 or result > 125:
            logger.warning('Unexpected ship level')
            result = 0
        return result


class ShipExp(Ocr):
    def __init__(self, buttons, lang='azur_lane', letter=(255, 255, 255), threshold=64, alphabet='0123456789IDSBM/',
                 name=None):
        super().__init__(buttons, lang=lang, letter=letter, threshold=threshold, alphabet=alphabet, name=name)

    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('I', '1').replace('D', '0').replace('S', '5')
        result = result.replace('B', '8')
        return result

    def ocr(self, image, direct_ocr=False):
        """
        Do OCR on a exp info, such as `100000/205000` or `3000000/Max`.

        Args:
            image:
            direct_ocr:

        Returns:
            list, int: exp digit, or a list of it.
        """
        result_list = super().ocr(image, direct_ocr=direct_ocr)
        result = result_list[0] if isinstance(result_list, list) else result_list

        result = re.search(r'(\d+)/', result)
        if result:
            result = [int(s) for s in result.groups()]
            current = int(result[0])
            return current
        else:
            logger.warning(f'Unexpected ocr result: {result_list}')
            return 0

def ship_info_get_level_exp(main, skip_first_screenshot=True):
    """
    Get ship level and exp from image.

    Args:
        image: Image to do OCR on.

    Returns:
        ShipLevel: Ship level and exp.
    """
    ocr_exp = ShipExp(OCR_SHIP_EXP, name='ShipExp')
    ocr_level = ShipLevel(OCR_SHIP_LEVEL, name='ShipLevel')
    timeout = Timer(2, count=4).start()
    level = 0
    exp = 0
    while 1:
        if skip_first_screenshot:
            skip_first_screenshot = False
        else:
            main.device.screenshot()
        
        level = ocr_level.ocr(main.device.image)
        exp = ocr_exp.ocr(main.device.image)
        
        if timeout.reached():
            logger.warning('ship_info_get_level_exp timeout')
            return level, exp
        if level > 0:
            if exp > 0:
                return level, exp
            else:
                continue