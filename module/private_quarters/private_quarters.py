import module.config.server as server
from module.base.timer import Timer
from module.handler.assets import POPUP_CANCEL
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from module.private_quarters.assets import *
from module.ui.page import page_private_quarters
from module.ui.ui import UI

OCR_DAILY_COUNT = DigitCounter(PRIVATE_QUARTERS_DAILY_COUNT, letter=(255, 247, 247), threshold=64)
if server.server != 'jp':
    OCR_SHOP_GOLD_COINS = Digit(PRIVATE_QUARTERS_SHOP_GOLD_COINS, letter=(239, 239, 239), name='OCR_SHOP_GOLD_COINS')
else:
    OCR_SHOP_GOLD_COINS = Digit(PRIVATE_QUARTERS_SHOP_GOLD_COINS, letter=(201, 201, 201), name='OCR_SHOP_GOLD_COINS')

class PrivateQuarters(UI):
    # Key: str, target ship name
    # Value: Button, button instance
    available_targets = {
        'anchorage': PRIVATE_QUARTERS_SHIP_ANCHORAGE,
        'noshiro': PRIVATE_QUARTERS_SHIP_NOSHIRO,
        'sirius': PRIVATE_QUARTERS_SHIP_SIRIUS,
    }

    def _pq_target_appear(self):
        """
        Callable wrapper to validate target's appearance
        offset=(100, 100) detectable for anchorage, noshiro, and sirus
        When more ships added may need to adjust or capture specific bubble position per
        ship, can use the available_targets to store similarly into tuples instead
        """
        settle_timer = Timer(1.5, count=3).start()
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End, success
            if self.appear(PRIVATE_QUARTERS_ROOM_TARGET_CHECK, offset=(100, 100)):
                return True

            # End, failed expired wait time
            if settle_timer.reached():
                return False

    def _pq_goto_room_check(self):
        """
        Callable wrapper for whether is loading or blocked by download asset popup
        """
        return self.appear(PRIVATE_QUARTERS_LOADING_CHECK, offset=(20,20)) or self.appear(POPUP_CANCEL, offset=(20, 20))

    def _pq_goto_room_enter(self, target_ship):
        """
        Execute enter room routine

        Args:
            target_ship (str):

        Returns:
            bool
        """
        # Initiate goto into target's room
        # Ensure either loading or popup
        # prompt appears after click
        target_title = target_ship.title()
        target_btn = self.available_targets[target_ship]
        self.ui_click(
            click_button=target_btn,
            check_button=self._pq_goto_room_check,
            appear_button=page_private_quarters.check_button,
            offset=(20, 20),
            skip_first_screenshot=True)

        # If was download asset popup
        # Terminate the run
        if self.handle_popup_cancel('PRIVATE_QUARTERS_DOWNLOAD_ASSET', offset=(20, 20)):
            logger.error(f'Cannot enter {target_title}\'s room, please download the necessary assets first')
            return False

        # Fully enter into target's room
        # through click progression
        click_timer = Timer(1.5, count=3).start()
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(PRIVATE_QUARTERS_ROOM_CHECK, offset=(20, 20)):
                break

            # Continue without clicking, mitigate too many click exception
            if self.appear(PRIVATE_QUARTERS_LOADING_CHECK, offset=(20, 20)):
                continue

            if click_timer.reached():
                self.device.click(PRIVATE_QUARTERS_ROOM_SAFE_CLICK_AREA)
                click_timer.reset()

        # If target's intimacy is maxed
        # Terminate the run
        if self.appear(PRIVATE_QUARTERS_ROOM_TARGET_INTIMACY_MAX, offset=(20, 20)):
            logger.warn(f'{target_title}\'s intimacy is maxed, configure to new target or turn off subtask altogether')
            return False

        return True

    def _pq_goto_room_exit(self):
        """
        Execute room exit routine
        """
        self.interval_clear(PRIVATE_QUARTERS_ROOM_BACK)
        self.ui_click(
            click_button=PRIVATE_QUARTERS_ROOM_BACK,
            check_button=page_private_quarters.check_button,
            offset=(20, 20),
            retry_wait=1.5,
            skip_first_screenshot=True
        )
        self.handle_info_bar()

    def _pq_shop_exit(self):
        """
        Execute shop exit routine
        """
        self.ui_click(
            click_button=PRIVATE_QUARTERS_SHOP_BACK,
            check_button=page_private_quarters.check_button,
            offset=(20, 20),
            skip_first_screenshot=True
        )

    def pq_shop_weekly_roses(self):
        """
        Execute purchase weekly roses from shop routine
        Must have 24K+, try next day if low
        """
        # Enter shop
        self.ui_click(
            click_button=PRIVATE_QUARTERS_SHOP_ENTER,
            check_button=PRIVATE_QUARTERS_SHOP_CHECK,
            appear_button=page_private_quarters.check_button,
            offset=(20, 20),
            skip_first_screenshot=True
        )

        # Roses available for purchase?
        # Exit shop if not
        # Noticeable lag observed on appearance of roses
        appear_timer = Timer(1.5, count=3).start()
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End, no roses
            if appear_timer.reached():
                logger.info('No more weekly roses to purchase, exit subtask')
                self._pq_shop_exit()
                return

            # End, has roses
            if self.appear(PRIVATE_QUARTERS_SHOP_WEEKLY_ROSES_CHECK, offset=(20, 20)):
                break

        # Read coins, exit if < 24000 (total price for all roses)
        # Try again next day if low
        currency = OCR_SHOP_GOLD_COINS.ocr(self.device.image)
        if currency < 24000:
            logger.warn(f'Have: {currency}, Need: 24000. Try again next day')
            return
        logger.info('Purchasing all available weekly roses')

        # Execute purchase operation
        skip_first_screenshot=True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(PRIVATE_QUARTERS_SHOP_WEEKLY_ROSES_GET, offset=(20, 20), interval=1):
                self.device.click(PRIVATE_QUARTERS_SHOP_BACK)
                break

            if self.appear_then_click(PRIVATE_QUARTERS_SHOP_WEEKLY_ROSES_CHECK, offset=(20, 20), interval=1):
                continue
            if self.appear_then_click(PRIVATE_QUARTERS_SHOP_AMOUNT_MAX, offset=(20, 20), interval=1):
                continue
            if self.appear_then_click(PRIVATE_QUARTERS_SHOP_CONFIRM_AMOUNT, offset=(20, 20), interval=1):
                continue

        # Exit shop
        self._pq_shop_exit()


    def pq_interact(self):
        """
        Execute target interact routine
        """
        click_iteration = 0
        click_timer = Timer(1.5, count=3).start()
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if click_iteration > 2 and self.appear(PRIVATE_QUARTERS_INTERACT, offset=(20, 20)):
                break

            if click_timer.reached():
                self.device.click(PRIVATE_QUARTERS_ROOM_TARGET_CLICK_AREA)
                click_timer.reset()
            if self.appear_then_click(PRIVATE_QUARTERS_INTERACT, offset=(20, 20), interval=1):
                click_timer.reset()
            if self.appear(PRIVATE_QUARTERS_INTERACT_CHECK, offset=(20, 20), interval=1):
                self.device.click(PRIVATE_QUARTERS_ROOM_BACK)
                click_timer.reset()
                click_iteration += 1

        self._pq_goto_room_exit()

    def pq_goto_room(self, target_ship, retry=3):
        """
        Execute goto target's room routine
        Try again if target absent in initial load
        Limit to at most configured 'retry' count

        Args:
            target_ship (str):
            retry  (int):
        """
        success = False
        target_title = target_ship.title()

        for _ in range(retry):
            if not self._pq_goto_room_enter(target_ship):
                break

            if self._pq_target_appear():
                logger.info(f'{target_title} is waiting and excited for your arrival!')
                success = True
                break
            logger.warn(f'{target_title} is not ready, exit and try again; retry={retry - (_ + 1)}')

            self._pq_goto_room_exit()

        return success

    def pq_run(self, buy_roses, target_interact, target_ship):
        """
        Execute daily private quarters routine
        - Purchase weekly roses from shop
        - Interact with target ship girl

        Args:
            buy_roses       (bool):
            target_interact (bool):
            target_ship     (str):
        """
        logger.info('Private Quarters run')

        # Enter shop and spend coin for weekly roses if enabled
        if buy_roses:
            self.pq_shop_weekly_roses()

        # Interact with target if enabled
        if target_interact:
            # Pull count here, exit run if = 0
            count, _, _ = OCR_DAILY_COUNT.ocr(self.device.image)
            if count == 0:
                logger.info('Daily intimacy count exhausted, exit subtask')
                return

            # Verify target is a valid selectable
            target_title = target_ship.title()
            if target_ship not in self.available_targets:
                logger.error(f'Unsupported target ship: {target_title}, cannot continue subtask')
                return

            # Handle if target is not in initial load
            # Limit to 3 tries
            if not self.pq_goto_room(target_ship, retry=3):
                return

            # Execute 'interact' routine
            self.pq_interact()

    def run(self):
        """
        Pages:
            in: Any page
            out: page_main, may have info_bar
        """
        self.ui_goto(page_private_quarters, get_ship=False)
        self.handle_info_bar()

        self.pq_run(
            buy_roses=self.config.PrivateQuarters_BuyRoses,
            target_interact=self.config.PrivateQuarters_TargetInteract,
            target_ship=self.config.PrivateQuarters_TargetShip
        )

        self.config.task_delay(server_update=True)