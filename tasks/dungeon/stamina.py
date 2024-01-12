import module.config.server as server
from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import Digit
from tasks.base.page import page_guide
from tasks.dungeon.assets.assets_dungeon_stamina import *
from tasks.dungeon.ui import DungeonUI


class DungeonStamina(DungeonUI):
    def _immersifier_enter(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_guide, Survival_Index, Simulated_Universe
            out: IMMERSIFIER_CHECK
        """
        logger.info('Enter immersifier')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(IMMERSIFIER_CHECK):
                break
            if self.appear_then_click(ENTER_IMMERSIFIER, interval=2):
                continue

    def _immersifier_exit(self, skip_first_screenshot=True):
        """
        Pages:
            in: IMMERSIFIER_CHECK
            out: page_guide, Survival_Index, Simulated_Universe
        """
        logger.info('Exit immersifier')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.ui_page_appear(page_guide):
                break
            if self.handle_reward():
                continue
            if self.handle_popup_cancel():
                continue

    def _item_amount_set(
            self,
            amount: int,
            ocr_button: ButtonWrapper,
            minus_button=AMOUNT_MINUS,
            plus_button=AMOUNT_PLUS,
            skip_first_screenshot=True,
    ):
        logger.info(f'Item amount set to {amount}')
        ocr = Digit(ocr_button, lang=server.lang)
        interval = Timer(1, count=3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            current = ocr.ocr_single_line(self.device.image)
            if not current:
                continue
            # End
            if current == amount:
                logger.info(f'At target amount')
                break
            # Click
            if interval.reached():
                diff = amount - current
                if diff > 0:
                    _ = self.appear(plus_button)  # Search button
                    self.device.multi_click(plus_button, n=abs(diff))
                    interval.reset()
                elif diff < 0:
                    _ = self.appear(minus_button)  # Search button
                    self.device.multi_click(minus_button, n=abs(diff))
                    interval.reset()
                else:
                    logger.error(f'Invalid world diff: {diff}')

    def _item_confirm(self, skip_first_screenshot=True):
        """
        Pages:
            in: POPUP_CONFIRM
            out: page_guide
        """
        # POPUP_CONFIRM -> reward_appear()
        timeout = Timer(2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.reward_appear():
                break
            if self.ui_page_appear(page_guide):
                if timeout.reached():
                    logger.warning('Wait item popup timeout')
                    break
            else:
                timeout.reset()

            if self.handle_popup_confirm():
                continue

        # reward_appear() -> page_guide
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.ui_page_appear(page_guide):
                break
            if self.handle_reward():
                continue

    def immersifier_store(self, max_store: int = 0):
        """
        Store immersifiers using all trailblaze power

        Args:
            max_store: Maximum amount to store this time

        Returns:
            int: Amount stored

        Pages:
            in: Any
            out: page_guide, Survival_Index, Simulated_Universe
        """
        logger.hr('Immersifier store', level=2)
        logger.info(f'Max store: {max_store}')
        self.dungeon_goto_rogue()
        self.dungeon_update_stamina()
        before = self.config.stored.Immersifier.value

        if self.config.stored.Immersifier.is_full():
            logger.info('Immersifier full, cannot store more')
            return False
        amount = min(
            self.config.stored.TrailblazePower.value // 40,
            self.config.stored.Immersifier.get_remain(),
        )
        if max_store:
            amount = min(amount, max_store)
        if amount <= 0:
            logger.info('Not enough stamina to store 1 immersifier')
            return 0

        self._immersifier_enter()
        self._item_amount_set(amount, ocr_button=OCR_IMMERSIFIER_AMOUNT)
        self._item_confirm()
        self.dungeon_update_stamina()
        diff = self.config.stored.Immersifier.value - before
        logger.info(f'Stored {diff} immersifiers')
        return diff
