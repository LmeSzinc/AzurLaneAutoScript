from module.base.timer import Timer
from module.base.utils import get_color
from module.logger import logger
from module.os_handler.assets import *
from module.os_handler.map_event import MapEventHandler
from module.ui.scroll import Scroll

STRATEGIC_SEARCH_SCROLL = Scroll(STRATEGIC_SEARCH_SCROLL_AREA, color=(247, 211, 66), name='STRATEGIC_SEARCH_SCROLL')


class StrategicSearchHandler(MapEventHandler):
    def strategy_search_enter(self, skip_first_screenshot=False):
        logger.info('Strategic search enter')
        self.interval_clear(STRATEGIC_SEARCH_MAP_OPTION_OFF)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(STRATEGIC_SEARCH_POPUP_CHECK, offset=(20, 20)):
                return True

            if self.handle_map_event():
                continue
            if self.appear(AUTO_SEARCH_REWARD, offset=(50, 50)):
                continue
            if self.match_template_color(STRATEGIC_SEARCH_MAP_OPTION_OFF, offset=(20, 20), interval=2):
                self.device.click(STRATEGIC_SEARCH_MAP_OPTION_OFF)
                continue

    def strategic_search_set_tab(self, skip_first_screenshot=False):
        logger.info('Strategic search set tab')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if get_color(self.device.image, STRATEGIC_SEARCH_TAB_SECURED.area)[2] <= 150:
                self.device.click(STRATEGIC_SEARCH_TAB_SECURED)
                continue
            if get_color(self.device.image, STRATEGIC_SEARCH_TAB_SECURED.area)[2] > 150:
                break

    def _strategy_search_scroll_appear(self, skip_first_screenshot=True):
        """
        Returns:
            bool: If it still exists
        """
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if STRATEGIC_SEARCH_SCROLL.appear(main=self):
                return True
            else:
                logger.warning('STRATEGIC_SEARCH_SCROLL disappeared')
            if timeout.reached():
                logger.warning('STRATEGIC_SEARCH_SCROLL disappeared confirm')
                return False

    def strategic_search_set_option(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Returns:
            If success. False if strategic settings closed for unknown reason.
        """
        logger.info('Strategic search set option')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(STRATEGIC_SEARCH_ZONEMODE_RANDOM):
                logger.attr('zone_mode', 'random')
                self.device.click(STRATEGIC_SEARCH_ZONEMODE_REPEAT)
            if self.appear(STRATEGIC_SEARCH_MERCHANT_CONTINUE):
                logger.attr('encounter_merchant', 'continue')
                self.device.click(STRATEGIC_SEARCH_MERCHANT_STOP)
                continue
            if self.appear(STRATEGIC_SEARCH_ZONEMODE_REPEAT) \
                    and self.appear(STRATEGIC_SEARCH_MERCHANT_STOP):
                logger.attr('zone_mode', 'repeat')
                logger.attr('encounter_merchant', 'stop')
                skip_first_screenshot = True
                break

        STRATEGIC_SEARCH_SCROLL.drag_threshold = 0.1
        STRATEGIC_SEARCH_SCROLL.set(0.5, main=self)
        if not self._strategy_search_scroll_appear():
            return False

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            self.appear(STRATEGIC_SEARCH_DEVICE_CHECK, offset=(20, 200), similarity=0.7)
            STRATEGIC_SEARCH_DEVICE_STOP.load_offset(STRATEGIC_SEARCH_DEVICE_CHECK)
            STRATEGIC_SEARCH_DEVICE_CONTINUE.load_offset(STRATEGIC_SEARCH_DEVICE_CHECK)

            if self.image_color_count(STRATEGIC_SEARCH_DEVICE_CONTINUE.button, color=(156, 255, 82), count=30):
                logger.attr('encounter_device', 'continue')
                self.device.click(STRATEGIC_SEARCH_DEVICE_STOP)
                continue
            if self.image_color_count(STRATEGIC_SEARCH_DEVICE_STOP.button, color=(156, 255, 82), count=30):
                logger.attr('encounter_device', 'stop')
                skip_first_screenshot = True
                break

        STRATEGIC_SEARCH_SCROLL.drag_threshold = 0.05
        STRATEGIC_SEARCH_SCROLL.edge_add = (0.5, 0.8)
        STRATEGIC_SEARCH_SCROLL.set_bottom(main=self)
        if not self._strategy_search_scroll_appear():
            return False

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            self.appear(STRATEGIC_SEARCH_SUBMIT_CHECK, offset=(20, 20), similarity=0.7)
            STRATEGIC_SEARCH_SUBMIT_OFF.load_offset(STRATEGIC_SEARCH_SUBMIT_CHECK)
            STRATEGIC_SEARCH_SUBMIT_ON.load_offset(STRATEGIC_SEARCH_SUBMIT_CHECK)

            if self.image_color_count(STRATEGIC_SEARCH_SUBMIT_OFF.button, color=(156, 255, 82), count=30):
                logger.attr('auto_submit', 'off')
                self.device.click(STRATEGIC_SEARCH_SUBMIT_ON)
                continue
            if self.image_color_count(STRATEGIC_SEARCH_SUBMIT_ON.button, color=(156, 255, 82), count=30):
                logger.attr('auto_submit', 'on')
                break

        return True

    def strategic_search_confirm(self, skip_first_screenshot=False):
        logger.info('Strategic search confirm')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(STRATEGIC_SEARCH_POPUP_CHECK, offset=(20, 20)) \
                    and self.handle_popup_confirm(offset=(30, 30), name='STRATEGIC_SEARCH'):
                continue

            if self.is_in_map():
                return True

    def strategic_search_start(self, skip_first_screenshot=False):
        """
        Returns:
            If success.

        Pages:
            in: IN_MAP
            out: IN_MAP, with strategic search running
        """
        logger.hr('Strategic search start')
        for _ in range(3):
            self.strategy_search_enter(skip_first_screenshot=skip_first_screenshot)
            self.strategic_search_set_tab(skip_first_screenshot=True)
            success = self.strategic_search_set_option(skip_first_screenshot=True)
            if not success:
                continue
            self.strategic_search_confirm(skip_first_screenshot=True)
            return True

        logger.warning('Failed to start strategic search')
        return False
