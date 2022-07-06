from module.base.decorator import cached_property
from module.base.timer import Timer
from module.logger import logger
from module.shipyard.assets import *
from module.shipyard.ui_globals import *
from module.ui.navbar import Navbar
from module.ui.assets import SHIPYARD_CHECK
from module.ui.ui import UI


class ShipyardUI(UI):
    def _shipyard_cannot_strengthen(self):
        """
        Shorthand for appear if a ship can no longer
        be strengthened either in 'DEV' or 'FATE'
        interface

        Returns:
            bool if appear
        """
        if self.appear(SHIPYARD_PROGRESS_DEV, offset=(20, 20)) \
                or self.appear(SHIPYARD_PROGRESS_FATE, offset=(20, 20)) \
                or self.appear(SHIPYARD_LEVEL_NOT_ENOUGH_FATE, offset=(20, 20)) \
                or self.appear(SHIPYARD_LEVEL_NOT_ENOUGH_DEV, offset=(20, 20)):
            logger.info('Ship at full strength for current level, '
                        'no more BPs can be consumed')
            return True
        return False

    def _shipyard_get_append(self):
        """
        Shorthand to get the appropriate append/post-fix

        Returns:
            string 'FATE' or 'DEV'
        """
        if self.appear(SHIPYARD_IN_FATE, offset=(20, 20)):
            return 'FATE'
        else:
            return 'DEV'

    def _shipyard_get_total(self):
        """
        Retrieve read total value
        in current game screen; dynamic
        UI varies between PR season

        Returns:
            Button, Button, int (ocr read value)
        """
        # Game UI is messy here. Situation varies with DEV/FATE and MAX button.
        # Having a MAX button is like:
        # | - |   0   | + | | MAX |
        # Not having a MAX button is like:
        # | - |       0       | + |
        # Here make a dynamic detection, and produce new ocr area.
        append = self._shipyard_get_append()
        ocr = globals()[f'OCR_SHIPYARD_TOTAL_{append}']
        minus = globals()[f'SHIPYARD_MINUS_{append}']
        plus = globals()[f'SHIPYARD_PLUS_{append}']
        self.wait_until_appear(minus, offset=(20, 20), skip_first_screenshot=True)
        self.wait_until_appear(plus, offset=(150, 20), skip_first_screenshot=True)
        area = ocr.buttons[0]
        ocr.buttons = [(minus.button[2] + 3, area[1], plus.button[0] - 3, area[3])]

        return plus, minus, ocr.ocr(self.device.image)

    def _shipyard_ensure_index(self, count, skip_first_screenshot=True):
        """
        Primitive 'ui_ensure_index'-like implementation

        Try to adjust for all of count if interface allows
        for it otherwise leave as the number allowed

        Args:
            count (int): Target number to ensure index

        Returns:
            int remaining BPs that cannot be consumed
        """
        if count < 0:
            logger.warning('_shipyard_ensure_index --> Non-positive '
                           '\'count\' cannot continue')
            return None

        current = diff = 0
        for _ in range(3):
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            plus, minus, current = self._shipyard_get_total()
            if current == count:
                logger.info(f'Capable of consuming all {count} BPs')
                return 0

            diff = count - current
            button = plus if diff > 0 else minus
            self.device.multi_click(button, n=diff, interval=(0.3, 0.5))
            self.device.sleep((0.3, 0.5))

        logger.info(f'Current interface does not allow consumption of {count} BPs\n')
        logger.info(f'Capable of consuming at most {current} of the {count} BPs')
        return diff

    def _shipyard_get_bp_count(self, index=0):
        """
        Args:
            index (int): Target index's BP count

        Returns:
            Ocr'ed count for index
        """
        # index(config.SHIPYARD_INDEX) start from 1
        # Base Case
        if index <= 0 or index > len(SHIPYARD_BP_COUNT_GRID.buttons):
            logger.warning(f'Cannot parse for count from index {index}')
            return -1

        result = OCR_SHIPYARD_BP_COUNT_GRID.ocr(self.device.image)

        return result[index - 1]

    def _shipyard_in_ui(self):
        """
        Returns:
            bool whether in appropriate shipyard ui area
        """
        if self.appear(SHIPYARD_CHECK, offset=(20, 20)):
            return True
        if self.appear(SHIPYARD_IN_DEV, offset=(20, 20)):
            return True
        if self.appear(SHIPYARD_IN_FATE, offset=(20, 20)):
            return True

        return False

    def _shipyard_set_series(self, series=1, skip_first_screenshot=True):
        """
        Args:
            series (int): Target research series to set view
            skip_first_screenshot (bool):

        Returns:
            bool whether successful
        """
        # Base Case
        if series <= 0 or series > len(SHIPYARD_SERIES_GRID.buttons):
            logger.warning(f'Research Series {series} is not selectable')
            return False

        self.ui_click(SHIPYARD_SERIES_SELECT_ENTER, appear_button=self._shipyard_in_ui,
                      check_button=SHIPYARD_SERIES_SELECT_CHECK,
                      skip_first_screenshot=skip_first_screenshot)
        series_button = SHIPYARD_SERIES_GRID.buttons[series - 1]
        self.ui_click(series_button, appear_button=SHIPYARD_SERIES_SELECT_CHECK,
                      check_button=self._shipyard_in_ui,
                      skip_first_screenshot=skip_first_screenshot)

        return True

    @cached_property
    def _shipyard_bottom_navbar(self):
        """
        Shipyard bottom nav bar used to switch between ships within a selected series
        Location varies on own's research progress, so users
        must verify the index for themselves
        """
        return Navbar(grids=SHIPYARD_FACE_GRID,
                      active_color=(33, 113, 222), active_threshold=221, active_count=50,
                      inactive_color=(49, 60, 82), inactive_threshold=221, inactive_count=50)

    def shipyard_bottom_navbar_ensure(self, left=None, right=None, skip_first_screenshot=True):
        """
        Ensure transition to target ship's page in interface
        according to index

        Args:
            left (int):
            right (int):
            skip_first_screenshot (bool):

        Returns:
            bool, whether Navbar was successfully set
        """
        if left is None and right is not None:
            left = right
            right = None
        if left is not None:
            if left <= 0 or left > len(SHIPYARD_FACE_GRID.buttons):
                logger.warning(f'Index for bottom Navbar {left} is not selectable')
                return False

        ensured = False
        if self._shipyard_bottom_navbar.set(self, left=left, right=right, skip_first_screenshot=skip_first_screenshot):
            ensured = True

        # After navbar set, wait until
        # full transition for delayed assets
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self._shipyard_in_ui():
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

        return ensured

    def shipyard_set_focus(self, series=1, index=1, skip_first_screenshot=True):
        """
        Args:
            series (int): Target research series to set view
            index (int): Target index to set view
            skip_first_screenshot (bool):

        Returns:
            bool whether successful
        """
        if series > 2 and index > 5:
            logger.warning(f'Research Series {series} is limited to indexes 1-5, cannot set focus to index {index}')
            return False
        return self._shipyard_set_series(series, skip_first_screenshot) and \
            self.shipyard_bottom_navbar_ensure(left=index, skip_first_screenshot=skip_first_screenshot)

    def _shipyard_get_ship(self, skip_first_screenshot=True):
        """
        Handles screen transitions to get the completely
        researched ship

        Args:
            skip_first_screenshot (bool):
        """
        from module.combat.assets import GET_SHIP

        confirm_timer = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(SHIPYARD_RESEARCH_COMPLETE,
                                      interval=1, offset=(20, 20)):
                confirm_timer.reset()
                continue

            if self.story_skip():
                confirm_timer.reset()
                continue

            if self.appear_then_click(GET_SHIP, interval=1):
                confirm_timer.reset()
                continue

            if self.handle_popup_confirm('LOCK_SHIP'):
                confirm_timer.reset()
                continue

            if self.appear(SHIPYARD_CONFIRM_DEV, offset=(20, 20)):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

    def _shipyard_buy_confirm(self, text, skip_first_screenshot=True):
        """
        Handles screen transitions to use/buy BPs

        Args:
            text (str): for handle_popup_confirm
            skip_first_screenshot (bool):
        """
        success = False
        append = self._shipyard_get_append()
        button = globals()[f'SHIPYARD_CONFIRM_{append}']
        ocr_timer = Timer(10, count=10).start()
        confirm_timer = Timer(1, count=2).start()
        self.interval_clear(button)

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if ocr_timer.reached():
                logger.warning('Failed to detect for normal exit routine, resort to OCR check')
                _, _, current = self._shipyard_get_total()
                if not current:
                    logger.info('Confirm action has completed, setting flag for exit')
                    self.interval_reset(button)
                    success = True
                ocr_timer.reset()
                continue

            if self.appear_then_click(button, offset=(20, 20), interval=3):
                continue

            if self.handle_popup_confirm(text):
                self.interval_reset(button)
                ocr_timer.reset()
                confirm_timer.reset()
                continue

            if self.story_skip():
                self.interval_reset(button)
                success = True
                ocr_timer.reset()
                confirm_timer.reset()
                continue

            if self.handle_info_bar():
                self.interval_reset(button)
                success = True
                ocr_timer.reset()
                confirm_timer.reset()
                continue

            # End
            if success and \
                self._shipyard_in_ui():
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

    def _shipyard_buy_enter(self):
        """
        Transitions to appropriate buying interface

        Returns:
            bool whether entered
        """
        if self.appear(SHIPYARD_RESEARCH_INCOMPLETE, offset=(20, 20)) or \
           self.appear(SHIPYARD_RESEARCH_IN_PROGRESS, offset=(20, 20)):
            logger.warning('Cannot enter buy interface, focused '
                           'ship has not yet been fully researched')
            return False

        if self.appear(SHIPYARD_RESEARCH_COMPLETE, offset=(20, 20)):
            self._shipyard_get_ship()

        if self.appear(SHIPYARD_GO_FATE, offset=(20, 20)):
            self.device.click(SHIPYARD_GO_FATE)
            self.wait_until_appear(SHIPYARD_IN_FATE, offset=(20, 20))

        return True
