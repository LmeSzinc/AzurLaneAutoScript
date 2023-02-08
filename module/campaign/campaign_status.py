import re

import cv2
import numpy as np

from module.base.timer import Timer
from module.campaign.assets import OCR_EVENT_PT, OCR_COIN, OCR_OIL, OCR_GEM, OCR_COIN_LIMIT, OCR_OIL_LIMIT
from module.logger import logger
from module.ocr.ocr import Ocr, Digit
from module.ui.ui import UI
from module.log_res.log_res import LogRes

OCR_OIL = Digit(OCR_OIL, name='OCR_OIL', letter=(247, 247, 247), threshold=128)
OCR_COIN = Digit(OCR_COIN, name='OCR_COIN', letter=(239, 239, 239), threshold=128)
OCR_OIL_LIMIT = Digit(OCR_OIL_LIMIT, name='OCR_OIL_LIMIT', letter=(235, 235, 235), threshold=128)
OCR_COIN_LIMIT = Digit(OCR_COIN_LIMIT, name='OCR_COIN_LIMIT', letter=(239, 239, 239), threshold=128)


class PtOcr(Ocr):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, lang='azur_lane', alphabet='X0123456789', **kwargs)

    def pre_process(self, image):
        """
        Args:
            image (np.ndarray): Shape (height, width, channel)

        Returns:
            np.ndarray: Shape (width, height)
        """
        # Use MAX(r, g, b)
        r, g, b = cv2.split(cv2.subtract((255, 255, 255, 0), image))
        image = cv2.min(cv2.min(r, g), b)
        # Remove background, 0-192 => 0-255
        image = cv2.multiply(image, 255 / 192)

        return image.astype(np.uint8)


OCR_PT = PtOcr(OCR_EVENT_PT)


class CampaignStatus(UI):
    def get_event_pt(self):
        """
        Returns:
            int: PT amount, or 0 if unable to parse
        """
        pt = OCR_PT.ocr(self.device.image)

        res = re.search(r'X(\d+)', pt)
        if res:
            pt = int(res.group(1))
            logger.attr('Event_PT', pt)
            LogRes(self.config).log_res('Pt', {'Value': pt})
            return pt
        else:
            logger.warning(f'Invalid pt result: {pt}')
            LogRes(self.config).log_res('Pt', {'Value': 0})
            return 0

    def get_coin(self, skip_first_screenshot=True):
        """
        Returns:
            int: Coin amount
        """
        amount = 0
        limit = 0
        timeout = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Get coin timeout')
                break

            amount = OCR_COIN.ocr(self.device.image)
            limit = OCR_COIN_LIMIT.ocr(self.device.image)
            if amount >= 100:
                break
        LogRes(self.config).log_res('Coin', {'Value': amount, 'Limit': limit})

        return amount

    def _get_oil(self):
        return OCR_OIL.ocr(self.device.image)

    def get_oil(self, skip_first_screenshot=True):
        """
        Returns:
            int: Oil amount
        """
        amount = 0
        limit = 0
        timeout = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Get oil timeout')
                break

            amount = OCR_OIL.ocr(self.device.image)
            limit = OCR_OIL_LIMIT.ocr(self.device.image)
            if amount >= 100:
                break
        LogRes(self.config).log_res('Oil', {'Value': amount, 'Limit': limit})

        return amount
