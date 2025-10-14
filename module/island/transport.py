from datetime import datetime, timedelta

from module.base.utils import area_offset
from module.island.assets import *
from module.island.ui import IslandUI
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.ocr.ocr import Duration


class IslandTransport:
    # index of transport commission
    index: int
    # If success to parse transport commission
    valid: bool
    # Duration to run this transport commission
    duration: timedelta
    # Status of transport commission
    # Value: finished, running, pending, unknown
    status: str

    def __init__(self, main, index):
        self.index = index
        self.valid = True
        self.duration = None
        self.can_start = True
        self.parse_transport(main)
        if not self.valid:
            self.can_start = False
        self.create_time = datetime.now()

    def parse_transport(self, main):
        offset = (-20, -20, 20, 20)
        delta = 176
        self.offset = area_offset(offset, (0, delta * self.index))

        # commission locked
        lock_offset = area_offset(offset, (0, delta * (self.index - 1)))
        if self.index >= 1 and main.appear(TRANSPORT_LOCKED, lock_offset):
            self.valid = False
            return

        self.status = self.get_transport_status(main)
        if self.status == 'unknown':
            self.valid = False
            return
        elif self.status == 'pending':
            button = OCR_TRANSPORT_TIME.move((0, self.offset[1] + 20))
            ocr = Duration(button, lang='cnocr', letter=(207, 207, 207), name='OCR_TRANSPORT_TIME')
            self.duration = ocr.ocr(main.device.image)
            if not self.duration.total_seconds():
                self.valid = False
                return

            if not main.match_template_color(TRANSPORT_START, offset=self.offset):
                self.can_start = False
                return
        elif self.status == 'running':
            self.can_start = False

            button = OCR_TRANSPORT_TIME_REMAIN.move((0, self.offset[1] + 20))
            ocr = Duration(button, name='OCR_TRANSPORT_TIME')
            self.duration = ocr.ocr(main.device.image)
            if not self.duration.total_seconds():
                self.valid = False
                return
        elif self.status == 'finished':
            self.can_start = False

    def get_transport_status(self, main):
        if main.appear(TRANSPORT_STATUS_PENDING, offset=self.offset):
            return 'pending'
        elif main.appear(TRANSPORT_STATUS_RUNNING, offset=self.offset):
            return 'running'
        elif main.appear(TRANSPORT_RECEIVE, offset=self.offset):
            return 'finished'
        else:
            return 'unknown'

    def convert_to_running(self):
        if self.valid:
            self.status = 'running'
            self.create_time = datetime.now()

    @property
    def finish_time(self):
        if self.valid:
            return (self.create_time + self.duration).replace(microsecond=0)
        else:
            return None

    def __str__(self):
        if not self.valid:
            return f'Index: {self.index} (Invalid)'
        info = {'Index': self.index, 'Status': self.status}
        if self.duration:
            info['Duration'] = self.duration
        info['can_start'] = self.can_start
        info = ', '.join([f'{k}: {v}' for k, v in info.items()])
        return info


class IslandTransportRun(IslandUI):
    def _transport_detect(self):
        """
        Get all commissions from self.device.image.

        Returns:
            SelectedGrids:
        """
        logger.hr('Transport Commission detect')
        commission = []
        for index in range(3):
            comm = IslandTransport(main=self, index=index)
            logger.attr(f'Transport Commission', comm)
            commission.append(comm)
        return SelectedGrids(commission)

    def transport_detect(self, trial=1, skip_first_screenshot=True):
        """
        Get all transport missions from self.device.image.

        Args:
            trial (int): Retry if has one invalid commission.
            skip_first_screenshot (bool):

        Returns:
            SelectedGrids:
        """
        commissions = SelectedGrids([])
        for _ in range(trial):
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            commissions = self._transport_detect()
            if commissions.count >= 2 and commissions.select(valid=False).count == 1:
                logger.warning('Found 1 invalid commission, retry commission detect')
                continue
            else:
                return commissions.select(valid=True)

        logger.info('trials of transport commission detect exhausted, stop')
        return commissions.select(valid=True)

    def island_transport_run(self):
        logger.hr('Island Transport Run', level=1)
        future_finish = []
        commissions = self.transport_detect(trial=2)

        future_finish = sorted([f for f in commissions.select(status='running').get('finish_time') if f is not None])
        logger.info(f'Transport finish: {[str(f) for f in future_finish]}')
        if not len(future_finish):
            logger.info('No island transport running')
        return future_finish
