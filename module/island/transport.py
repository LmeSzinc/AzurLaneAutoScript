from datetime import datetime, timedelta
import numpy as np
import re

from cached_property import cached_property

from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.base.utils import area_offset, crop, image_color_count, rgb2gray
from module.island.assets import *
from module.island.ui import IslandUI
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.ocr.ocr import Duration
from module.ui_white.assets import POPUP_CANCEL_WHITE, POPUP_CONFIRM_WHITE


class IslandTransport:
    # index of transport commission
    index: int
    # If success to parse transport commission
    valid: bool
    # If the commission is locked
    locked: bool
    # Duration to run this transport commission
    duration: timedelta
    # Status of transport commission
    # Value: finished, running, pending, refreshing, unknown
    status: str
    # If the transprt commission need to start
    start: bool
    # If the transprt commission need to refresh
    refresh: bool

    def __init__(self, main, index, blacklist):
        """
        Args:
            main:
            index (int):
            blacklist (list[Template]): a blacklist of templates of items to submit
        """
        self.index = index
        self.blacklist = blacklist
        self.image = main.device.image
        self.valid = True
        self.locked = False
        self.duration = None
        self.start = True
        self.refresh = False
        self.items = SelectedGrids([])
        self.parse_transport(main)
        if not self.valid:
            self.start = False
        self.create_time = datetime.now()

    def parse_transport(self, main):
        offset = (-20, -20, 20, 20)
        delta = 176
        self.offset = area_offset(offset, (0, delta * self.index))

        # commission locked
        lock_offset = area_offset(offset, (0, delta * (self.index - 1)))
        if self.index >= 1 and main.appear(TRANSPORT_LOCKED, lock_offset):
            self.locked = True
            return

        self.status = self.get_transport_status(main)
        if self.status == 'unknown':
            self.valid = False
            return
        elif self.status == 'pending':
            button = OCR_TRANSPORT_TIME.move((0, self.offset[1] + 20))
            ocr = Duration(button, lang='cnocr', letter=(207, 207, 207), name='OCR_TRANSPORT_TIME')
            self.duration = ocr.ocr(self.image)
            if not self.duration.total_seconds():
                self.valid = False
                return

            # items info
            origin_y = 174 + delta * self.index
            grids = ButtonGrid(origin=(481, origin_y), delta=(105, 0), 
                               button_shape=(86, 86), grid_shape=(3, 1), name='ITEMS')
            self.items = SelectedGrids([TransportItem(self.image, button, self.blacklist)
                                        for button in grids.buttons]).select(valid=True)
            self.start = self.items.select(load=True).count == self.items.count
            self.refresh = main.appear(TRANSPORT_REFRESH, offset=self.offset) and \
                           bool(self.items.select(refresh=True).count)

            # detect items first because we need to get refresh info
            if not main.match_template_color(TRANSPORT_START, offset=self.offset):
                self.start = False
        elif self.status == 'running':
            self.start = False
            button = OCR_TRANSPORT_TIME_REMAIN.move((0, self.offset[1] + 20))
            ocr = Duration(button, name='OCR_TRANSPORT_TIME')
            self.duration = ocr.ocr(self.image)
            if not self.duration.total_seconds():
                self.valid = False
                return
        elif self.status == 'finished':
            self.start = False
        elif self.status == 'refreshing':
            self.start = False
            button = OCR_TRANSPORT_REFRESH.move((0, self.offset[1] + 20))
            ocr = Duration(button, letter=(63, 64, 66), name='OCR_TRANSPORT_REFRESH')
            self.duration = ocr.ocr(self.image)
            if not self.duration.total_seconds():
                self.valid = False
                return

    def get_transport_status(self, main):
        if main.appear(TRANSPORT_STATUS_PENDING, offset=self.offset):
            return 'pending'
        elif main.appear(TRANSPORT_STATUS_RUNNING, offset=self.offset):
            return 'running'
        elif main.appear(TRANSPORT_RECEIVE, offset=self.offset):
            return 'finished'
        elif main.appear(TRANSPORT_REFRESH_CHECK, offset=self.offset):
            return 'refreshing'
        else:
            return 'unknown'

    def convert_to_refreshing(self):
        if self.valid:
            self.status = 'refreshing'
            self.start = False
            self.refresh = False
            self.duration = timedelta(hours=0, minutes=30, seconds=0)
            self.create_time = datetime.now()

    def convert_to_running(self):
        if self.valid:
            self.status = 'running'
            self.start = False
            self.refresh = False
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
        if self.locked:
            return f'Index: {self.index} (Locked)'
        info = {'Index': self.index, 'Status': self.status}
        if self.duration:
            info['Duration'] = self.duration
        info['Start'] = self.start
        info['Refresh'] = self.refresh
        info = ', '.join([f'{k}: {v}' for k, v in info.items()])
        return info

class TransportItem:
    # If the item is enough to submit and not in blacklist
    load: bool
    # If the item is in blacklist
    refresh: bool

    def __init__(self, image, button, blacklist):
        """
        Args:
            image:
            button:
            blacklist:
        """
        self.image_raw = image
        self.button = button
        self.blacklist = blacklist
        self.image = crop(image, button.area)
        self.valid = self.predict_valid()
        self.refresh = False
        self.load = self.predict_load()

    def predict_valid(self):
        # gray item means an empty item
        mean = np.mean(np.max(self.image, axis=2) > 234)
        # blue bar on top of the item means already loaded
        blue_bar_check = image_color_count(self.image[:10, :, :], color=(90, 201, 255), threshold=221, count=500)
        return mean > 0.3 and not blue_bar_check

    def predict_load(self):
        if not self.valid:
            return False
        self.refresh = self.handle_blacklist_items()
        if self.refresh:
            return False
        if not TEMPLATE_ITEM_SATISFIED.match(rgb2gray(self.image)):
            return False
        return True

    def handle_blacklist_items(self):
        """
        Check if current item is a blacklist item.

        Returns:
            bool: if any blacklist item
        """
        for template in self.blacklist:
            if template.match(self.image):
                return True
        return False

    def __str__(self):
        if not self.valid:
            return '(Invalid)'
        info = {'Load': self.load, 'Refresh': self.refresh}
        info = ', '.join([f'{k}: {v}' for k, v in info.items()])
        return info

class IslandTransportRun(IslandUI):
    @cached_property
    def blacklist(self):
        blacklist = []
        for k, v in self.config.cross_get(keys='Island.IslandTransport').items():
            if k.startswith('Submit') and not v:
                item = k.split('Submit')[-1]
                item = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', item)
                item = re.sub('([a-z0-9])([A-Z])', r'\1_\2', item)
                blacklist.append(globals()[f'TEMPLATE_{item.upper()}'])
        return blacklist

    def _transport_detect(self):
        """
        Get all commissions from self.device.image.

        Returns:
            SelectedGrids:
        """
        logger.hr('Transport Commission detect')
        commission = []
        for index in range(3):
            comm = IslandTransport(main=self, index=index, blacklist=self.blacklist)
            logger.attr(f'Transport Commission', comm)
            for item in comm.items:
                logger.attr(item.button, item)
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
            if not commissions.count:
                logger.warning('No commission detected, retry commission detect')
                continue
            elif commissions.select(valid=False).count:
                logger.warning('Found 1 invalid commission at least, retry commission detect')
                continue
            else:
                return commissions.select(valid=True)

        logger.info('trials of transport commission detect exhausted, stop')
        return commissions.select(valid=True)

    def transport_receive(self, skip_first_screenshot=True):
        """
        Receive all transport missions from transport page.

        Args:
            skip_first_screenshot (bool):

        Returns:
            bool: if received
        """
        logger.hr('Island Transport', level=2)
        self.device.click_record_clear()
        self.interval_clear([GET_ITEMS_ISLAND, TRANSPORT_RECEIVE, POPUP_CANCEL_WHITE])
        success = True
        click_timer = Timer(5, count=10).start()
        confirm_timer = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_info_bar():
                click_timer.reset()
                confirm_timer.reset()
                continue

            if self.appear_then_click(TRANSPORT_RECEIVE, offset=(-20, -20, 20, 400), interval=2):
                success = False
                click_timer.reset()
                confirm_timer.reset()
                continue

            if self.handle_get_items():
                success = True
                click_timer.reset()
                confirm_timer.reset()
                continue

            if self.handle_popup_cancel('REFRESH_CANCEL', offset=(30, 30)):
                click_timer.reset()
                confirm_timer.reset()
                continue

            # handle island level up
            if click_timer.reached():
                success = True
                self.device.click(GET_ITEMS_ISLAND)
                self.device.sleep(0.3)
                click_timer.reset()
                confirm_timer.reset()
                continue

            if self.island_in_transport():
                if success and confirm_timer.reached():
                    break
                click_timer.reset()
            else:
                confirm_timer.reset()

        return success

    def transport_refresh(self, comm, skip_first_screenshot=True):
        """
        Refresh the specific transport mission from transport page.

        Args:
            comm (IslandTransport): the commission to refresh
            skip_first_screenshot (bool):

        Returns:
            bool: if success
        """
        logger.info('Transport commission refresh')
        self.interval_clear([TRANSPORT_REFRESH, POPUP_CONFIRM_WHITE])
        success = True
        confirm_timer = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(TRANSPORT_REFRESH, offset=comm.offset, interval=2):
                continue

            if self.handle_popup_confirm('REFRESH_CONFIRM', offset=(30, 30)):
                success = True
                confirm_timer.reset()
                continue

            if self.island_in_transport():
                if success and confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()
        return success

    def transport_start(self, comm, skip_first_screenshot=True):
        """
        Start the specific transport mission from transport page.

        Args:
            comm (IslandTransport): the commission to start
            skip_first_screenshot (bool):

        Returns:
            bool: if success
        """
        logger.info('Transport commission start')
        self.interval_clear([GET_ITEMS_ISLAND, TRANSPORT_START, POPUP_CANCEL_WHITE])
        success = True
        confirm_timer = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(TRANSPORT_START, offset=comm.offset, interval=2):
                success = False
                confirm_timer.reset()
                continue

            if self.handle_get_items():
                success = True
                confirm_timer.reset()
                continue

            if self.handle_popup_cancel('REFRESH_CANCEL', offset=(30, 30)):
                confirm_timer.reset()
                continue

            if self.island_in_transport():
                if success and confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()
        return success

    def island_transport_run(self):
        """
        Execute island run to receive and start transport commissions.

        Returns:
            list[timedelta]: future finish timedelta
        """
        logger.hr('Island Transport Run', level=1)
        future_finish = []
        self.transport_receive()
        commissions = self.transport_detect(trial=5)

        comm_refresh = commissions.select(status='pending', refresh=True)
        comm_choose = commissions.select(status='pending', start=True)
        for comm in comm_refresh:
            if self.transport_refresh(comm):
                comm.convert_to_refreshing()
        for comm in comm_choose:
            if self.transport_start(comm):
                comm.convert_to_running()

        logger.hr('Showing transport commission', level=2)
        for comm in commissions:
            logger.attr(f'Transport Commission', comm)

        running_finish = [f for f in commissions.select(status='running').get('finish_time') if f is not None]
        refreshing_finish = [f for f in commissions.select(status='refreshing').get('finish_time') if f is not None]
        future_finish = sorted(running_finish + refreshing_finish)
        logger.info(f'Transport finish: {[str(f) for f in future_finish]}')
        if not len(future_finish):
            logger.info('No island transport running')
        return future_finish
