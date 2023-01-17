from module.base.timer import Timer
from module.combat.assets import GET_SHIP
from module.exception import ScriptError
from module.gacha.assets import *
from module.gacha.ui import GachaUI
from module.handler.assets import POPUP_CONFIRM, STORY_SKIP
from module.logger import logger
from module.ocr.ocr import Digit
from module.retire.retirement import Retirement
from module.shop.shop_general import GeneralShop

RECORD_GACHA_OPTION = ('RewardRecord', 'gacha')
RECORD_GACHA_SINCE = (0,)
OCR_BUILD_CUBE_COUNT = Digit(BUILD_CUBE_COUNT, letter=(255, 247, 247), threshold=64)
OCR_BUILD_TICKET_COUNT = Digit(BUILD_TICKET_COUNT, letter=(255, 247, 247), threshold=64)
OCR_BUILD_SUBMIT_COUNT = Digit(BUILD_SUBMIT_COUNT, letter=(255, 247, 247), threshold=64)
OCR_BUILD_SUBMIT_WW_COUNT = Digit(BUILD_SUBMIT_WW_COUNT, letter=(255, 247, 247), threshold=64)


class RewardGacha(GachaUI, GeneralShop, Retirement):
    build_cube_count = 0
    build_ticket_count = 0

    def gacha_prep(self, target, skip_first_screenshot=True):
        """
        Initiate preparation to submit build orders.

        Args:
            target (int): Number of build orders to submit
            skip_first_screenshot (bool):

        Returns:
            bool: True if prep complete otherwise False.

        Pages:
            in: page_build (any)
            out: submit pop up

        Except:
            May exit if unable to process prep
        """
        # Nothing to prep if 'target' = 0
        if not target:
            return False

        # Ensure correct page to be able to prep in
        if not self.appear(BUILD_SUBMIT_ORDERS) \
                and not self.appear(BUILD_SUBMIT_WW_ORDERS):
            return False

        # Use 'appear' to update actual position of assets
        # for ui_ensure_index
        confirm_timer = Timer(1, count=2).start()
        ocr_submit = None
        index_offset = (60, 20)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(BUILD_SUBMIT_ORDERS, interval=3):
                ocr_submit = OCR_BUILD_SUBMIT_COUNT
                confirm_timer.reset()
                continue

            if self.appear_then_click(BUILD_SUBMIT_WW_ORDERS, interval=3):
                ocr_submit = OCR_BUILD_SUBMIT_WW_COUNT
                confirm_timer.reset()
                continue

            # End
            if self.appear(BUILD_PLUS, offset=index_offset) \
                    and self.appear(BUILD_MINUS, offset=index_offset):
                if confirm_timer.reached():
                    break

        # Check for exception, exited prematurely
        # Apply appropriate submission count
        if ocr_submit is None:
            raise ScriptError('Failed to identify ocr asset required, '
                              'cannot continue prep work')
        area = ocr_submit.buttons[0]
        ocr_submit.buttons = [(BUILD_MINUS.button[2] + 3, area[1], BUILD_PLUS.button[0] - 3, area[3])]
        self.ui_ensure_index(target, letter=ocr_submit, prev_button=BUILD_MINUS,
                             next_button=BUILD_PLUS, skip_first_screenshot=True)

        return True

    def gacha_calculate(self, target_count, gold_cost, cube_cost):
        """
        Calculate number able to actually submit.

        Args:
            target_count (int): Number of build orders like to submit
            gold_cost (int): Gold coin cost
            cube_cost (int): Cube cost

        Returns:
            int: Actual number able to submit based on current resources
        """
        while 1:
            # Calculate cost of resources based on 'target_count'
            gold_total = gold_cost * target_count
            cube_total = cube_cost * target_count

            # Reached 0, cannot execute gacha roll
            if not target_count:
                logger.warning('Insufficient gold and/or cubes to gacha roll')
                break

            # Insufficient resources, reduce by 1 and re-calculate
            if gold_total > self._currency or cube_total > self.build_cube_count:
                target_count -= 1
                continue

            break

        # Modify resources, return current 'target_count'
        logger.info(f'Able to submit up to {target_count} build orders')
        self._currency -= gold_total
        self.build_cube_count -= cube_total
        return target_count

    def gacha_goto_pool(self, target_pool):
        """
        Transition to appropriate build pool page.

        Args:
            target_pool (str): Name of pool, default to
            'light' path if outside of acceptable range

        Returns:
            str: Current pool location based on availability

        Pages:
            in: page_build (gacha pool selection)
            out: page_build (gacha pool allowed)

        Except:
            May exit if 'wishing_well' but not
            complete configuration
        """
        # Switch view to 'light' pool
        self.gacha_bottom_navbar_ensure(right=3, is_build=True)

        # Transition to 'target_pool' if needed, update
        # 'target_pool' appropriately
        if target_pool == 'wishing_well':
            if self._gacha_side_navbar.get_total(main=self) != 5:
                logger.warning('\'wishing_well\' is not available, '
                               'default to \'light\' pool')
                target_pool = 'light'
            else:
                self.gacha_side_navbar_ensure(upper=2)
                if self.appear(BUILD_WW_CHECK):
                    raise ScriptError('\'wishing_well\' must be configured '
                                      'manually by user, cannot continue '
                                      'gacha_goto_pool')
        elif target_pool == 'event':
            gacha_bottom_navbar = self._gacha_bottom_navbar(is_build=True)
            if gacha_bottom_navbar.get_total(main=self) == 3:
                logger.warning('\'event\' is not available, default '
                               'to \'light\' pool')
                target_pool = 'light'
            else:
                self.gacha_bottom_navbar_ensure(left=1, is_build=True)
        elif target_pool in ['heavy', 'special']:
            if target_pool == 'heavy':
                self.gacha_bottom_navbar_ensure(right=2, is_build=True)
            else:
                self.gacha_bottom_navbar_ensure(right=1, is_build=True)

        return target_pool

    def gacha_flush_queue(self, skip_first_screenshot=True):
        """
        Flush build order queue to ensure empty before submission.

        Args:
            skip_first_screenshot (bool):

        Pages:
            in: page_build (any)
            out: page_build (gacha pool selection)

        Except:
            May exit if unable to flush queue entirely,
            dock likely full
        """
        # Go to Gacha/Orders page
        self.gacha_side_navbar_ensure(bottom=3)

        # Transition appropriate screens
        # and end up in Gacha/Build page
        confirm_timer = Timer(1, count=2).start()
        confirm_mode = True  # Drill, Lock Ship
        # Clear button offset, or will click at the PLUS button of gems or HOME button
        STORY_SKIP.clear_offset()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(BUILD_FINISH_ORDERS, interval=3):
                confirm_timer.reset()
                continue

            if self.handle_retirement():
                confirm_timer.reset()
                continue

            if self.handle_popup_confirm('FINISH_ORDERS'):
                if confirm_mode:
                    self.device.sleep((0.5, 0.8))
                    self.device.click(BUILD_FINISH_ORDERS)  # Skip animation, safe area
                    confirm_mode = False
                confirm_timer.reset()
                continue

            if self.appear(GET_SHIP, interval=1):
                self.device.click(STORY_SKIP)  # Fast forward for multiple orders
                confirm_timer.reset()
                continue

            if self.appear(BUILD_FINISH_RESULTS, offset=(20, 150), interval=3):
                self.device.click(BUILD_FINISH_ORDERS)  # Safe area
                confirm_timer.reset()
                continue

            # End, goes back to pool page if clicked with queue empty
            if self.appear(BUILD_SUBMIT_ORDERS) or self.appear(BUILD_SUBMIT_WW_ORDERS):
                if confirm_timer.reached():
                    break

    def gacha_submit(self, skip_first_screenshot=True):
        """
        Pages:
            in: POPUP_CONFIRM
            out: BUILD_FINISH_ORDERS
        """
        logger.info('Submit gacha')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(POPUP_CONFIRM, offset=(20, 80), interval=3):
                # Alter asset name for click
                POPUP_CONFIRM.name = POPUP_CONFIRM.name + '_' + 'GACHA_ORDER'
                self.device.click(POPUP_CONFIRM)
                POPUP_CONFIRM.name = POPUP_CONFIRM.name[:-len('GACHA_ORDER') - 1]
                continue

            # End
            if self.appear(BUILD_FINISH_ORDERS):
                break

    def gacha_run(self):
        """
        Run gacha operations to submit build orders.

        Returns:
            bool: True if run successful otherwise False

        Pages:
            in: any
            out: page_build
        """
        # Go to Gacha
        self.ui_goto_gacha()

        # Flush queue of any pre-existing
        # builds to ensure starting fresh
        # Upon exit, expected to be in
        # main Build page
        self.gacha_flush_queue()

        # OCR Gold and Cubes
        self.shop_currency()
        self.build_cube_count = OCR_BUILD_CUBE_COUNT.ocr(self.device.image)

        # Transition to appropriate target construction pool
        # Returns appropriate costs for gacha as well
        actual_pool = self.gacha_goto_pool(self.config.Gacha_Pool)

        # Determine appropriate cost based on gacha_goto_pool
        gold_cost = 600
        cube_cost = 1
        if actual_pool in ['heavy', 'special', 'event', 'wishing_well']:
            gold_cost = 1500
            cube_cost = 2

        # OCR build tickets, decide use cubes/coins or not
        # buy = [rolls_using_tickets, rolls_using_cubes]
        buy = [self.config.Gacha_Amount, 0]
        if actual_pool == "event" and self.config.Gacha_UseTicket:
            if self.appear(BUILD_TICKET_CHECK, offset=(30, 30)):
                self.build_ticket_count = OCR_BUILD_TICKET_COUNT.ocr(self.device.image)
            else:
                logger.info('Build ticket not detected, use cubes and coins')
        if self.config.Gacha_Amount > self.build_ticket_count:
            buy[0] = self.build_ticket_count
            # Calculate rolls allowed based on configurations and resources
            buy[1] = self.gacha_calculate(self.config.Gacha_Amount-self.build_ticket_count, gold_cost, cube_cost)

        # Submit 'buy_count' and execute if capable
        # Cannot use handle_popup_confirm, this window
        # lacks POPUP_CANCEL
        result = False
        for buy_count in buy:
            if self.gacha_prep(buy_count):
                self.gacha_submit()

                # If configured to use drill after build
                if self.config.Gacha_UseDrill:
                    self.gacha_flush_queue()
                # Return True if any submit successed
                result = True

        return result

    def run(self):
        """
        Handle gacha operations if configured to do so.

        Pages:
            in: Any page
            out: page_build
        """
        self.gacha_run()
        self.config.task_delay(server_update=True)
