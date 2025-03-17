from module.awaken.assets import *
from module.base.timer import Timer
from module.exception import ScriptError
from module.logger import logger
from module.ocr.ocr import Digit
from module.retire.dock import CARD_GRIDS, DOCK_EMPTY, Dock, SHIP_DETAIL_CHECK
from module.ui.assets import BACK_ARROW
from module.ui.page import page_dock, page_main


class ShipLevel(Digit):
    def after_process(self, result):
        result = super().after_process(result)
        if result < 100 or result > 125:
            logger.warning('Unexpected ship level')
            result = 0
        return result


class Awaken(Dock):
    def _get_button_state(self, button: Button):
        """
        Args:
            button: COST_COIN or COST_CHIP or COST_ARRAY

        Returns:
            bool: True if having sufficient resource, False if not
                or None if such resource is not required
        """
        # If COST_ARRAY is absent, COST_COIN and COST_CHIP are right moved 54px
        if button.match(self.device.image, offset=(75, 20)):
            # Look down, see if there are red letters
            area = button.button
            area = (area[0], area[3], area[2], area[3] + 60)
            if self.image_color_count(area, color=(214, 53, 33), threshold=180, count=16):
                return False
            else:
                return True
        else:
            return None

    def _get_awaken_cost(self, use_array=False):
        """
        Args:
            use_array: True to awaken to 125, False to 120

        Returns:
            bool or str:
                True if all required resource is sufficient,
                False if any is insufficient,
                'unexpected_array' if not going to use array but array presents,
                'invalid' if result valid,
        """
        coin = self._get_button_state(COST_COIN)
        chip = self._get_button_state(COST_CHIP)
        array = self._get_button_state(COST_ARRAY)

        logger.attr('AwakenCost', {'coin': coin, 'chip': chip, 'array': array})

        def is_right_moved(button):
            # If COST_ARRAY is absent, COST_COIN and COST_CHIP are right moved 54px
            return button.button[0] - button.area[0] > 20

        # Check if result are valid
        if array is not None:
            if not use_array:
                logger.warning('Not going to use array but array presents')
                return 'unexpected_array'
            # If array is needed, coin and chip should present
            if coin is not None and not is_right_moved(COST_COIN) \
                    and chip is not None and not is_right_moved(COST_CHIP):
                result = coin and chip and array
                logger.attr('AwakenSufficient', result)
                return result
        else:
            # If array is not needed, coin and chip should both present and right moved
            if coin is not None and is_right_moved(COST_COIN) \
                    and chip is not None and is_right_moved(COST_CHIP):
                result = coin and chip
                logger.attr('AwakenSufficient', result)
                return result

        logger.warning('Invalid awaken cost')
        return 'invalid'

    def handle_awaken_finish(self):
        return self.appear_then_click(AWAKEN_FINISH, offset=(20, 20), interval=1)

    def is_in_awaken(self):
        return SHIP_LEVEL_CHECK.match_luma(self.device.image, similarity=0.7)

    def awaken_popup_close(self, skip_first_screenshot=True):
        logger.info('Awaken popup close')
        self.interval_clear(AWAKEN_CANCEL)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.is_in_awaken():
                break
            if self.appear_then_click(AWAKEN_CANCEL, offset=(20, 20), interval=3):
                continue
            if self.handle_awaken_finish():
                continue

    def awaken_once(self, use_array=False, skip_first_screenshot=True):
        """
        Args:
            use_array:
            skip_first_screenshot:

        Returns:
            str: Result state, 'no_exp', 'unexpected_array', 'insufficient', 'timeout', 'success'

        Pages:
            in: is_in_awaken
            out: is_in_awaken
        """
        logger.hr('Awaken once', level=2)
        interval = Timer(3, count=6)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(AWAKEN_CONFIRM):
                break
            if LEVEL_UP.match_luma(self.device.image):
                logger.info(f'awaken_once ended at {LEVEL_UP}')
                return 'no_exp'
            # Lower similarity due to random background
            if interval.reached() and AWAKENING.match_luma(self.device.image, similarity=0.7):
                self.device.click(AWAKENING)
                interval.reset()
                continue

        logger.info('Get awaken cost')
        timeout = Timer(2, count=6).start()
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            result = self._get_awaken_cost(use_array)
            if result == 'unexpected_array':
                # This shouldn't happen
                self.awaken_popup_close()
                return result
            elif result is False:
                logger.info('Insufficient resources to awaken')
                self.awaken_popup_close()
                return 'insufficient'
            elif result is True:
                # Sufficient resources
                break
            elif result == 'invalid':
                # Retry, and check timeout also
                pass
            else:
                raise ScriptError(f'Unexpected _get_awaken_cost result: {result}')
            if timeout.reached():
                logger.warning('Get awaken cost timeout')
                self.awaken_popup_close()
                return 'timeout'

        # sufficient is True
        logger.info('Awaken confirm')
        self.interval_clear(AWAKEN_CONFIRM)
        # Awaken popup takes 10s to appear if you have enough EXP to reach next awaken limit
        # and 2s to dismiss it by clicking
        # Timeout here is very long
        timeout = Timer(30, count=30).start()
        finished = False
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if timeout.reached():
                logger.warning('Awaken confirm timeout')
                self.awaken_popup_close()
                break
            if finished and self.is_in_awaken():
                logger.info('Awaken finished')
                break
            # Click
            if self.appear_then_click(AWAKEN_CONFIRM, offset=(20, 20), interval=3):
                continue
            if self.handle_popup_confirm('AWAKEN'):
                continue
            if self.handle_awaken_finish():
                finished = True
                continue

        self.device.click_record_clear()
        return 'success'

    def get_ship_level(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Returns:
            int: 100~125, or 0 if error
        """
        ocr = ShipLevel(OCR_SHIP_LEVEL, letter=(255, 255, 255), threshold=128, name='ShipLevel')
        timeout = Timer(2, count=4).start()
        level = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.is_in_awaken():
                level = ocr.ocr(self.device.image)
                if level > 0:
                    return level
            if timeout.reached():
                logger.warning('get_ship_level timeout')
                return level

    def awaken_ship(self, use_array=False, skip_first_screenshot=True):
        """
        Awaken one ship til EXP not enough or reached stop level

        Args:
            use_array: True to awaken to level 125, False to 120
            skip_first_screenshot:

        Returns:
            str: 'level_max', 'insufficient', 'no_exp', 'timeout'

        Pages:
            in: is_in_awaken
            out: is_in_awaken
        """
        logger.hr('Awaken ship', level=1)
        logger.info(f'Awaken ship, use_array={use_array}')

        if use_array:
            stop_level = 125
        else:
            stop_level = 120

        if not skip_first_screenshot:
            self.device.screenshot()

        for _ in range(7):
            level = self.get_ship_level()
            if level > 0:
                if level >= stop_level:
                    logger.info(f'Awaken ship ended at stop_level')
                    return 'level_max'
                else:
                    result = self.awaken_once(use_array)
                    # 'no_exp', 'unexpected_array', 'insufficient', 'timeout', 'success'
                    if result == 'success':
                        continue
                    if result in ['insufficient', 'no_exp']:
                        # Return as it is
                        return result
                    if result == 'unexpected_array':
                        # Maybe just accidentally entered awaken confirm
                        # Re-run awaken_once should recheck it
                        continue
                    if result == 'timeout':
                        # Timeout getting resources, retry should fix it
                        continue
                    raise ScriptError(f'Unexpected awaken_once result: {result}')
            else:
                # Get level timeout, request exit
                return 'timeout'

        # Error, request exit
        logger.warning('Too many awaken trial on one ship')
        return 'timeout'

    def awaken_exit(self, skip_first_screenshot=True):
        """
        Pages:
            in: is_in_awaken
            out: DOCK_CHECK
        """
        logger.info('Awaken exit')
        interval = Timer(3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.ui_page_appear(page_dock):
                logger.info(f'Awaken exit at {page_dock}')
                break
            if interval.reached() and self.is_in_awaken():
                logger.info(f'is_in_awaken -> {BACK_ARROW}')
                self.device.click(BACK_ARROW)
                interval.reset()
                continue
            if self.handle_awaken_finish():
                continue
            if self.appear_then_click(AWAKEN_CANCEL, offset=(20, 20), interval=3):
                continue
            if self.is_in_main(interval=5):
                self.device.click(page_main.links[page_dock])
                continue

    def awaken_run(self, use_array=False):
        """
        Awaken all ships in dock until resources exhausted

        Args:
            use_array: True to awaken to level 125, False to 120

        Returns:
            str: 'insufficient', 'finish', 'timeout'

        Pages:
            in: Any
            out: page_dock
        """
        logger.hr('Awaken run', level=1)
        self.ui_ensure(page_dock)
        self.dock_favourite_set(wait_loading=False)
        self.dock_sort_method_dsc_set(wait_loading=False)
        if use_array:
            extra = ['can_awaken_plus']
        else:
            extra = ['can_awaken']
        self.dock_filter_set(extra=extra)

        while 1:
            # page_dock
            if self.appear(DOCK_EMPTY, offset=(20, 20)):
                logger.info('awaken_run finished, no ships to awaken')
                result = 'finish'
                break

            # page_dock -> SHIP_DETAIL_CHECK
            self.ship_info_enter(
                CARD_GRIDS[(0, 0)], check_button=SHIP_DETAIL_CHECK, long_click=False)

            # is_in_awaken
            result = self.awaken_ship(use_array)
            self.awaken_exit()
            # 'insufficient', 'no_exp', 'timeout'
            if result in ['no_exp', 'level_max']:
                # Awaken next ship
                continue
            if result == 'insufficient':
                logger.info('awaken_run finished, resources exhausted')
                break
            if result == 'timeout':
                logger.info(f'awaken_run finished, result={result}')
                break
            raise ScriptError(f'Unexpected awaken_ship result: {result}')

        return result

    def run(self):
        # Run Awakening+ first
        if self.config.Awaken_LevelCap == 'level125':
            # Use Cognitive Arrays
            result = self.awaken_run(use_array=True)
            # Use Cognitive Chips
            if result != 'timeout':
                self.awaken_run()
        elif self.config.Awaken_LevelCap == 'level120':
            # Use Cognitive Chips
            self.awaken_run()
        else:
            raise ScriptError(f'Unknown Awaken_LevelCap={self.config.Awaken_LevelCap}')

        # Reset dock filters
        logger.hr('Awaken run exit', level=1)
        self.dock_filter_set(wait_loading=False)

        # Scheduler
        self.config.task_delay(server_update=True)
