import re
from datetime import datetime

import cv2
import numpy as np

from module.base.decorator import cached_property
from module.campaign.assets import OCR_EVENT_PT
from module.config.utils import deep_get, DEFAULT_TIME
from module.logger import logger
from module.ocr.ocr import Ocr
from module.ui.ui import UI


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


class CampaignEvent(UI):
    @cached_property
    def campaign_pt_ocr(self):
        return PtOcr(OCR_EVENT_PT)

    def get_event_pt(self):
        """
        Returns:
            int: PT amount, or 0 if unable to parse
        """
        pt = self.campaign_pt_ocr.ocr(self.device.image)

        res = re.search('X(\d+)', pt)
        if res:
            pt = int(res.group(1))
            logger.attr('Event_PT', pt)
            return pt
        else:
            logger.warning(f'Invalid pt result: {pt}')
            return 0

    def _disable_tasks(self, tasks):
        """
        Args:
            tasks (list[str]): Task name
        """
        for task in tasks:
            keys = f'{task}.Scheduler.Enable'
            logger.info(f'Disable task `{task}`')
            self.config.modified[keys] = False

        for task in ['GemsFarming']:
            if deep_get(self.config.data, keys=f'{task}.Campaign.Event', default='campaign_main') != 'campaign_main':
                logger.info(f'Reset GemsFarming to 2-4')
                self.config.modified[f'{task}.Campaign.Name'] = '2-4'
                self.config.modified[f'{task}.Campaign.Event'] = 'campaign_main'

        logger.info(f'Reset event time limit')
        self.config.modified['EventGeneral.EventGeneral.TimeLimit'] = DEFAULT_TIME

        self.config.update()

    def event_pt_limit_triggered(self):
        """
        Returns:
            bool:

        Pages:
            in: page_event or page_sp
        """
        limit = int(self.config.EventGeneral_PtLimit)
        tasks = [
            'Event',
            'Event2',
            'EventAb',
            'EventB',
            'EventCd',
            'EventD',
            'EventSp',
            'Raid',
            'RaidDaily'
            'GemsFarming',
        ]
        command = self.config.Scheduler_Command
        if limit <= 0 or command not in tasks:
            return False
        if command == 'GemsFarming' and self.config.Campaign_Event == 'campaign_main':
            return False

        pt = self.get_event_pt()
        if pt >= limit:
            logger.hr(f'Reach event PT limit: {limit}')
            self._disable_tasks(tasks)
            return True
        else:
            return False

    def event_time_limit_triggered(self):
        """
        Returns:
            bool:

        Pages:
            in: page_event or page_sp
        """
        limit = self.config.EventGeneral_TimeLimit
        tasks = [
            'Event',
            'Event2',
            'EventAb',
            'EventB',
            'EventCd',
            'EventD',
            'EventSp',
            'GemsFarming',
            'Raid',
            'RaidDaily',
            'MaritimeEscort',
        ]
        command = self.config.Scheduler_Command
        if command not in tasks or limit == DEFAULT_TIME:
            return False
        if command == 'GemsFarming' and self.config.Campaign_Event == 'campaign_main':
            return False

        now = datetime.now()
        if now > limit:
            logger.hr(f'Reach event time limit: {limit}')
            self._disable_tasks(tasks)
            return True
        else:
            return False
