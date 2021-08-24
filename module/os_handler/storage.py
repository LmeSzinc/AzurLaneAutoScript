import numpy as np

from module.base.utils import rgb2gray
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2
from module.logger import logger
from module.os.globe_operation import GlobeOperation
from module.os.globe_zone import ZoneManager
from module.os_handler.assets import *
from module.ui.scroll import Scroll

SCROLL_STORAGE = Scroll(STORATE_SCROLL, color=(247, 211, 66))


class StorageHandler(GlobeOperation, ZoneManager):
    def storage_enter(self):
        """
        Pages:
            in: is_in_map, STORAGE_ENTER
            out: STORAGE_CHECK
        """
        self.ui_click(STORAGE_ENTER, check_button=STORAGE_CHECK, offset=(200, 5), skip_first_screenshot=True)
        self.handle_info_bar()

    def storage_quit(self):
        """
        Pages:
            in: STORAGE_CHECK
            out: is_in_map
        """
        self.ui_back(STORAGE_ENTER, offset=(200, 5), skip_first_screenshot=True)

    def _storage_logger_use(self, button, skip_first_screenshot=True):
        """
        Args:
            button (Button): Item
            skip_first_screenshot (bool):

        Pages:
            in: STORAGE_CHECK
            out: STORAGE_CHECK
        """
        success = False
        self.interval_clear(STORAGE_CHECK)
        self.interval_clear(STORAGE_USE)
        self.interval_clear(GET_ITEMS_1)
        self.interval_clear(GET_ITEMS_2)

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(STORAGE_CHECK, offset=(20, 20), interval=5):
                self.device.click(button)
                continue
            if self.appear_then_click(STORAGE_USE, offset=(180, 30), interval=5):
                self.interval_reset(STORAGE_CHECK)
                continue
            if self.appear_then_click(GET_ITEMS_1, interval=5):
                self.interval_reset(STORAGE_CHECK)
                success = True
                continue
            if self.appear_then_click(GET_ITEMS_2, interval=5):
                self.interval_reset(STORAGE_CHECK)
                success = True
                continue

            # End
            if success and self.appear(STORAGE_CHECK, offset=(20, 20)):
                break

    def storage_logger_use_all(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Pages:
            in: STORAGE_CHECK
            out: STORAGE_CHECK, scroll to bottom
        """
        logger.hr('Storage logger use all')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if SCROLL_STORAGE.appear(main=self):
                SCROLL_STORAGE.set_bottom(main=self, skip_first_screenshot=True)

            image = rgb2gray(np.array(self.device.image))
            items = TEMPLATE_STORAGE_LOGGER.match_multi(image, similarity=0.5)
            logger.attr('Storage_logger', len(items))

            if len(items):
                self._storage_logger_use(items[0])
                continue
            else:
                logger.info('All loggers in storage have been used')
                break

    def _storage_checkout(self, button, skip_first_screenshot=True):
        """
        Args:
            button (Button): Item
            skip_first_screenshot (bool):

        Pages:
            in: STORAGE_CHECK
            out: is_in_map, in an obscured zone.
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(STORAGE_CHECK, offset=(30, 30), interval=5):
                self.device.click(button)
            if self.appear_then_click(STORAGE_COORDINATE_CHECKOUT, offset=(30, 30), interval=5):
                self.interval_reset(STORAGE_CHECK)
                continue

            # End
            if self.is_zone_pinned():
                break

        self.zone_type_select('OBSCURE')
        self.globe_enter(zone=self.name_to_zone(72))

    def storage_checkout_obscure(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Returns:
            bool: If checkout

        Pages:
            in: STORAGE_CHECK
            out: is_in_map, in an obscured zone if checkout.
                 is_in_map, in previous zone if no more obscured coordinates.
        """
        logger.hr('Storage checkout obscured')
        if SCROLL_STORAGE.appear(main=self):
            SCROLL_STORAGE.set_top(main=self, skip_first_screenshot=skip_first_screenshot)

        image = rgb2gray(np.array(self.device.image))
        items = TEMPLATE_STORAGE_OBSCURED.match_multi(image, similarity=0.75)
        logger.attr('Storage_obscured', len(items))

        if not len(items):
            logger.info('No more obscured coordinates in storage')
            self.storage_quit()
            return False

        self._storage_checkout(items[0])
        return True

    def os_get_next_obscure(self, use_logger=True):
        """
        Args:
            use_logger: If use all loggers.

        Returns:
            bool: If checkout

        Pages:
            in: in_map
            out: is_in_map, in an obscured zone if checkout.
                 is_in_map, in previous zone if no more obscured coordinates.
        """
        logger.hr('OS get next obscure')
        self.storage_enter()
        if use_logger:
            self.storage_logger_use_all()
        result = self.storage_checkout_obscure()
        return result
