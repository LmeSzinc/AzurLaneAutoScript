import numpy as np

from module.base.utils import color_bar_percentage
from module.combat.assets import GET_ITEMS_1
from module.exception import ScriptError
from module.logger import logger
from module.retire.assets import *
from module.retire.dock import Dock, CARD_GRIDS


class Enhancement(Dock):
    @property
    def _retire_amount(self):
        if self.config.RETIRE_AMOUNT == 'all':
            return 2000
        if self.config.RETIRE_AMOUNT == '10':
            return 10
        return 10

    def _enhance_enter(self, favourite=False):
        if favourite:
            self.dock_favourite_set(enable=True)

        self.dock_filter_enter()
        self.dock_filter_index_enhance_set(enable=True)
        self.dock_filter_confirm()

        self.equip_enter(CARD_GRIDS[(0, 0)], check_button=SHIP_DETAIL_CHECK, long_click=False)

    def _enhance_quit(self):
        self.equip_quit(DOCK_FILTER)
        self.dock_favourite_set(enable=False)
        self.dock_filter_enter()
        self.dock_filter_index_all_set(enable=True)
        self.dock_filter_confirm()

    def _enhance_confirm(self):
        executed = False
        while 1:
            self.device.screenshot()

            # if self.appear_then_click(ENHANCE_CONFIRM, offset=(30, 30), interval=3):
            #     continue
            if self.appear_then_click(EQUIP_CONFIRM, offset=(30, 30), interval=3):
                continue
            if self.appear_then_click(EQUIP_CONFIRM_2, offset=(30, 30), interval=3):
                continue
            if self.appear(GET_ITEMS_1, interval=2):
                self.device.click(GET_ITEMS_1_RETIREMENT_SAVE)
                self.interval_reset(ENHANCE_CONFIRM)
                executed = True
                continue

            # End
            if executed and self.appear(ENHANCE_CONFIRM, offset=(30, 30)):
                self.ensure_no_info_bar()
                break

    def _enhance_choose(self, skip_first_screenshot=True):
        """
        Page require: page_ship_enhance, without info_bar
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(EQUIP_CONFIRM, offset=(30, 30)):
                return True

            self.equip_sidebar_ensure(index=4)
            self.wait_until_appear(ENHANCE_RECOMMEND, offset=(5, 5), skip_first_screenshot=True)

            status = color_bar_percentage(self.device.image, area=ENHANCE_RELOAD.area, prev_color=(231, 178, 74))
            logger.attr('Reload_enhanced', f'{int(status * 100)}%')
            choose = np.sum(np.array(self.device.image.crop(ENHANCE_FILLED.area)) > 200) > 100

            if self.info_bar_count():
                if status > 0.98:
                    logger.info('Fully enhanced for this ship')
                    self.equip_view_next(check_button=ENHANCE_RECOMMEND)
                    self.ensure_no_info_bar()
                    continue
                else:
                    if choose:
                        logger.info('Unable to enhance this ship')
                        self.equip_view_next(check_button=ENHANCE_RECOMMEND)
                        self.ensure_no_info_bar()
                        continue
                    else:
                        logger.info('Enhancement material exhausted')
                        return False

            if self.appear_then_click(ENHANCE_RECOMMEND, offset=(5, 5), interval=2):
                self.device.sleep(0.3)
                self.appear_then_click(ENHANCE_CONFIRM)

    def enhance_ships(self, favourite=None):
        """Page require: page_dock

        Args:
            favourite (bool):

        Returns:
            int: total enhanced
        """
        if favourite is None:
            favourite = self.config.ENHANCE_FAVOURITE

        logger.hr('Enhancement')
        logger.info(f'Favourite={favourite}')
        self._enhance_enter(favourite=favourite)
        total = 0

        while 1:
            if not self._enhance_choose():
                break
            self._enhance_confirm()
            total += 10
            if total >= self._retire_amount:
                break

        self._enhance_quit()
        return total

    def _enhance_handler(self):
        self.ui_click(RETIRE_APPEAR_3, check_button=DOCK_FILTER, skip_first_screenshot=True)
        self.handle_dock_cards_loading()

        total = self.enhance_ships()

        self.dock_quit()
        self.config.DOCK_FULL_TRIGGERED = True

        return total
