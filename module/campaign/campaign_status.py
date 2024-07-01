import re

import cv2
import numpy as np

from module.base.timer import Timer
from module.base.utils import color_similar, get_color
from module.campaign.assets import OCR_COIN, OCR_EVENT_PT, OCR_OIL, OCR_OIL_CHECK, OCR_COIN_LIMIT, OCR_OIL_LIMIT
from module.logger import logger
from module.ocr.ocr import Digit, Ocr
from module.shop.shop_status import OCR_SHOP_GEMS
from module.ui.ui import UI

OCR_COIN = Digit(OCR_COIN, name='OCR_COIN', letter=(239, 239, 239), threshold=128)
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
            return pt
        else:
            logger.warning(f'Invalid pt result: {pt}')
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

        self.config.stored.Coin.set(amount, limit)
        return amount

    def _get_oil(self):
        # Update offset
        _ = self.appear(OCR_OIL_CHECK)

        color = get_color(self.device.image, OCR_OIL_CHECK.button)
        if color_similar(color, OCR_OIL_CHECK.color):
            # Original color
            ocr_oil = Digit(OCR_OIL, name='OCR_OIL', letter=(247, 247, 247), threshold=128)
            ocr_oil_limit = Digit(OCR_OIL_LIMIT, name='OCR_OIL_LIMIT', letter=(247, 247, 247), threshold=128)
        elif color_similar(color, (59, 59, 64)):
            # With black overlay
            ocr_oil = Digit(OCR_OIL, name='OCR_OIL', letter=(165, 165, 165), threshold=128)
            ocr_oil_limit = Digit(OCR_OIL_LIMIT, name='OCR_OIL_LIMIT', letter=(165, 165, 165), threshold=128)
        else:
            logger.warning(f'Unexpected OCR_OIL_CHECK color')
            ocr_oil = Digit(OCR_OIL, name='OCR_OIL', letter=(247, 247, 247), threshold=128)
            ocr_oil_limit = Digit(OCR_OIL_LIMIT, name='OCR_OIL_LIMIT', letter=(247, 247, 247), threshold=128)

        return ocr_oil.ocr(self.device.image), ocr_oil_limit.ocr(self.device.image)

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

            if not self.appear(OCR_OIL_CHECK, offset=(10, 2)):
                logger.info('No oil icon')
                continue

            amount, limit = self._get_oil()
            if amount >= 100:
                break

        self.config.stored.Oil.set(amount, limit)
        return amount

    def status_get_gems(self):
        amount = OCR_SHOP_GEMS.ocr(self.device.image)
        self.config.stored.Gem.value = amount
        return amount

    def is_balancer_task(self):
        """
        Returns:
             bool: If is event task but not daily event task
        """
        tasks = [
            'Event',
            'Event2',
            'Raid',
            'Coalition',
            'GemsFarming',
        ]
        command = self.config.Scheduler_Command
        if command in tasks:
            if self.config.Campaign_Event == 'campaign_main':
                return False
            else:
                return True
        else:
            return False
