from random import choice

import module.config.server as server
from module.base.timer import Timer
from module.combat.assets import GET_ITEMS_1
from module.exception import GameStuckError, ScriptError
from module.logger import logger
from module.ocr.ocr import DigitCounter
from module.retire.assets import *
from module.retire.dock import CARD_GRIDS, Dock

VALID_SHIP_TYPES = ['dd', 'ss', 'cl', 'ca', 'bb', 'cv', 'repair', 'others']
if server.server != 'jp':
    OCR_DOCK_AMOUNT = DigitCounter(
        DOCK_AMOUNT, letter=(255, 255, 255), threshold=192)
else:
    OCR_DOCK_AMOUNT = DigitCounter(
        DOCK_AMOUNT, letter=(201, 201, 201), threshold=192)


class Enhancement(Dock):
    @property
    def _retire_amount(self):
        if self.config.Retirement_RetireMode == 'one_click_retire':
            return 3000
        if self.config.Retirement_RetireMode == 'old_retire':
            if self.config.OldRetire_RetireAmount == 'retire_all':
                return 3000
            if self.config.OldRetire_RetireAmount == 'retire_10':
                return 10
        return 3000

    def _enhance_enter(self, favourite=False, ship_type=None):
        """
        Pages:
            in: page_dock
            out: page_ship_enhance

        Returns:
            bool: False with filter applied resulting
                  in empty dock.
                  Otherwise true with at least 1 card
                  available to be picked.
        """
        if favourite:
            self.dock_favourite_set(enable=True)

        if ship_type is not None:
            ship_type = str(ship_type)
            self.dock_filter_set(extra='enhanceable', index=ship_type)
        else:
            self.dock_filter_set(extra='enhanceable')

        if self.appear(DOCK_EMPTY, offset=(30, 30)):
            return False

        self.ship_info_enter(
            CARD_GRIDS[(0, 0)], check_button=SHIP_DETAIL_CHECK, long_click=False)
        return True

    def _enhance_quit(self):
        """
        Pages:
            in: page_ship_enhance
            out: page_dock
        """
        self.ui_back(DOCK_CHECK)
        self.dock_favourite_set(enable=False)
        self.dock_filter_set()

    def _enhance_confirm(self, skip_first_screenshot=True):
        """
        Pages:
            in: EQUIP_CONFIRM
            out: page_ship_enhance, without info_bar
        """

        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(EQUIP_CONFIRM, offset=(30, 30), interval=3):
                confirm_timer.reset()
                continue
            if self.appear_then_click(EQUIP_CONFIRM_2, offset=(30, 30), interval=3):
                confirm_timer.reset()
                continue
            if self.appear(GET_ITEMS_1, interval=2):
                self.device.click(GET_ITEMS_1_RETIREMENT_SAVE)
                self.interval_reset(ENHANCE_CONFIRM)
                confirm_timer.reset()
                continue

            # End
            if self.appear(ENHANCE_CONFIRM, offset=(30, 30)):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

    def _enhance_choose(self, ship_count, skip_first_screenshot=True):
        """
        Refactor the implementation.
        Divided the enhancement process into
        several state functions. Use a DFA method
        to call those functions according to
        current state. Each state corresponds to
        a function with the same name.

        Pages:
            in: page_ship_enhance
            out: page_ship_enhance

        Args:
            ship_count (int): ship_count, must be
            non-zero positive integer

        Returns:
            True if able to enhance otherwise False
            Always paired with current ship_count
        """
        need_to_skip: bool = False

        def state_enhance_check():
            # Check the base case, switch to ready if enhancement can continue
            nonlocal need_to_skip
            need_to_skip = False
            if ship_count <= 0:
                logger.info(
                    'Reached maximum number to check, exiting current category')
                return "state_enhance_exit"
            if not self.ship_side_navbar_ensure(bottom=4):
                return "state_enhance_check"

            self.wait_until_appear(ENHANCE_RECOMMEND, offset=(
                5, 5), skip_first_screenshot=True)
            return "state_enhance_ready"

        def state_enhance_ready():
            # Wait until ENHANCE_RECOMMEND appears
            if self.appear_then_click(ENHANCE_RECOMMEND, offset=(5, 5), interval=0.3):
                logger.info('Set enhancement material by recommendation.')
                return "state_enhance_recommend"

            return "state_enhance_ready"

        def state_enhance_recommend():
            # Judge if enhance material appeared
            if not EMPTY_ENHANCE_SLOT_PLUS.match(self.device.image):
                logger.info('Material found. Try enhancing...')
                return "state_enhance_attempt"
            elif self.info_bar_count():
                logger.info('No material found for enhancement.')
                logger.info(
                    'Enhancement failed. Swiping to next ship if feasible')
                return "state_enhance_fail"

            return "state_enhance_ready"

        def state_enhance_attempt():
            # Wait until ENHANCE_CONFIRM appears
            if (self.appear_then_click(ENHANCE_CONFIRM, offset=(5, 5), interval=0.3)
                    or self.appear(EQUIP_CONFIRM, offset=(30, 30))
                    or self.info_bar_count()
                    or self.handle_popup_confirm('ENHANCE')):
                return "state_enhance_confirm"

            return "state_enhance_attempt"

        def state_enhance_confirm():
            # Succeeded if EQUIP_CONFIRM appeared, otherwise failed
            if self.appear(EQUIP_CONFIRM, offset=(30, 30)):
                logger.info('Enhancement Successful')
                self._enhance_confirm()
                return "state_enhance_success"
            elif self.info_bar_count():
                logger.info(
                    'Enhancement impossible, ship currently in battle. Swiping to next ship if feasible')
                nonlocal need_to_skip
                need_to_skip = True
                return "state_enhance_fail"
            elif self.handle_popup_confirm('ENHANCE'):
                logger.info('Trying a temporary ship')
                return "state_enhance_confirm"

            return "state_enhance_attempt"

        def state_enhance_fail():
            # Avoid a misjudgement caused by broken network
            if self.appear(EQUIP_CONFIRM, offset=(30, 30)):
                return "state_enhance_confirm"

            # Try to swipe to next
            if self.ship_view_next(check_button=ENHANCE_RECOMMEND):
                if not need_to_skip:
                    nonlocal ship_count
                    ship_count -= 1
                return "state_enhance_check"
            else:
                # Avoid a misjudgement caused by broken network
                if self.appear(EQUIP_CONFIRM, offset=(30, 30)):
                    return "state_enhance_confirm"
                else:
                    logger.info('Swiped failed, exiting current category')
                    return "state_enhance_exit"

        def state_enhance_success():
            return True

        def state_enhance_exit():
            return False

        state = "state_enhance_check"
        state_list = []
        while isinstance(state, str):
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            logger.info(f'Call state function: {state}')

            if state == "state_enhance_check":
                # Avoid too_many_click exception caused by multiple tries without material
                if state_list[-2:] == ["state_enhance_recommend", "state_enhance_fail"]:
                    while self.device.click_record and (self.device.click_record[-1] in ['ENHANCE_RECOMMEND', 'SHIP_SWIPE']):
                        self.device.click_record.pop()
                # Avoid too_many_click exception caused by enhancement failure on in-battle ships
                elif state_list[-3:] == ["state_enhance_attempt", "state_enhance_confirm", "state_enhance_fail"]:
                    while self.device.click_record and (self.device.click_record[-1] in ['ENHANCE_RECOMMEND', 'SHIP_SWIPE', 'ENHANCE_CONFIRM']):
                        self.device.click_record.pop()
                state_list.clear()
            state_list.append(state)
            if len(state_list) > 30:
                logger.critical(f'Too many state transitions: {state_list}')
                raise GameStuckError('Too many state transitions')

            try:
                state = locals()[state]()
            except KeyError as e:
                logger.warning(f'Unknown state function: {state}')
                raise ScriptError(f'Unknown state function: {state}')

        return state, ship_count

    def enhance_ships(self, favourite=None):
        """
        Enhance target ships by specified order
        of types listed in ENHANCE_ORDER_STRING

        Invalid types are treated as requesting
        from ALAS to choose a valid one at random

        Pages:
            in: page_dock
            out: page_dock

        Args:
            favourite (bool):

        Returns:
            int: total enhanced
        """
        if favourite is None:
            favourite = self.config.Enhance_ShipToEnhance == 'favourite'

        logger.hr('Enhancement by type')
        total = 0

        # Process ENHANCE_ORDER_STRING if any into ship_types
        if self.config.Enhance_Filter is not None:
            ship_types = [s.strip().lower()
                          for s in self.config.Enhance_Filter.split('>')]
            ship_types = list(filter(''.__ne__, ship_types))
            if len(ship_types) == 0:
                ship_types = [None]
        else:
            ship_types = [None]
        logger.attr('Enhance Order', ship_types)

        # Process available ship types for choice randomization
        # Removing types that have already been specified by
        # ENHANCE_ORDER_STRING
        available_ship_types = VALID_SHIP_TYPES.copy()
        [available_ship_types.remove(s)
         for s in ship_types if s in available_ship_types]

        for ship_type in ship_types:
            # None check, do not execute if is None
            # Otherwise, select a type at random since
            # user has specified an unrecognized type
            if ship_type is not None and ship_type not in VALID_SHIP_TYPES:
                if len(available_ship_types) == 0:
                    logger.info(
                        'No more ship types for ALAS to choose from, skipping iteration')
                    continue
                ship_type = choice(available_ship_types)
                available_ship_types.remove(ship_type)

            logger.info(f'Favourite={favourite}, Ship Type={ship_type}')

            # Continue if at least 1 CARD_GRID is selectable
            # otherwise skip to next ship type
            if not self._enhance_enter(favourite=favourite, ship_type=ship_type):
                logger.hr(f'Dock Empty by ship type {ship_type}')
                continue

            current_count = self.config.Enhance_CheckPerCategory
            while 1:
                choose_result, current_count = self._enhance_choose(
                    ship_count=current_count)
                if not choose_result:
                    break
                total += 10
                if total >= self._retire_amount:
                    break
            self.ui_back(DOCK_CHECK)

        self._enhance_quit()
        return total

    def _enhance_handler(self):
        """
        Pages:
            in: RETIRE_APPEAR
            out:

        Returns:
            tuple(int, int): (enhance turn count, remaining dock amount)

        Pages:
            in: DOCK_CHECK
            out: the page before retirement popup
        """
        total = self.enhance_ships()
        _, remain, _ = OCR_DOCK_AMOUNT.ocr(self.device.image)

        self.dock_quit()
        self.config.DOCK_FULL_TRIGGERED = True

        return total, remain
