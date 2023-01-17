import re

import cv2
import numpy as np

from module.base.timer import Timer
from module.campaign.assets import OCR_EVENT_PT, OCR_COIN, OCR_OIL, OCR_GEM, OCR_MAXCOIN, OCR_MAXOIL
from module.logger import logger
from module.ocr.ocr import Ocr, Digit
from module.ui.ui import UI
from module.log_res.log_res import log_res

OCR_OIL = Digit(OCR_OIL, name='OCR_OIL', letter=(247, 247, 247), threshold=128)
OCR_COIN = Digit(OCR_COIN, name='OCR_COIN', letter=(239, 239, 239), threshold=128)
OCR_MAXOIL = Digit(OCR_MAXOIL, name='OCR_MAXOIL', letter=(235, 235, 235), threshold=128)
OCR_MAXCOIN = Digit(OCR_MAXCOIN, name='OCR_MAXCOIN', letter=(239, 239, 239), threshold=128)

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

OCR_GEM = Digit(OCR_GEM,letter=(239, 223, 82),threshold=128)

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
            log_res.log_res(self,pt,'pt')
            return pt
        else:
            logger.warning(f'Invalid pt result: {pt}')
            log_res.log_res(self,0,'pt')
            return 0

    def get_gem(self, skip_first_screenshot=True):
        """
        Returns:
            int: gem amount, or 0 if unable to parse
        """
        amount = 0
        timeout = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
                            
            if timeout.reached():
                logger.warning('Get gem timeout')
                break
                      
            amount = OCR_GEM.ocr(self.device.image)
            
            if amount >= 10:
                break
        log_res.log_res(self,amount,'gem')

        return amount

    def get_coin(self, skip_first_screenshot=True):
        """
        Returns:
            int: Coin amount
        """
        amount1 = 0
        amount2 = 0
        timeout = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Get coin timeout')
                break

            amount1 = OCR_COIN.ocr(self.device.image)
            amount2 = OCR_MAXCOIN.ocr(self.device.image)
            if amount1 >= 100:
                break
        log_res.log_res(self,f'{amount1} / {amount2}','cointomaxcoin')

        return amount1

    def _get_oil(self):
        return OCR_OIL.ocr(self.device.image)

    def get_oil(self, skip_first_screenshot=True):
        """
        Returns:
            int: Coin amount
        """
        amount1 = 0
        amount2 = 0
        timeout = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Get coin timeout')
                break

            amount1 = OCR_OIL.ocr(self.device.image)
            amount2 = OCR_MAXOIL.ocr(self.device.image)
            if amount1 >= 100:
                break
        log_res.log_res(self,f'{amount1} / {amount2}','oiltomaxoil')

        return amount1
