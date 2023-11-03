from typing import Callable

from module.base.base import ModuleBase
from module.logger import logger
from tasks.base.assets.assets_base_page import BACK, CLOSE
from tasks.base.assets.assets_base_popup import *


class PopupHandler(ModuleBase):
    def handle_reward(self, interval=5, click_button: ButtonWrapper = None) -> bool:
        """
        Args:
            interval:
            click_button: Set a button to click

        Returns:
            If handled.
        """
        if click_button is None:
            if self.appear_then_click(GET_REWARD, interval=interval):
                return True
        else:
            if self.appear(GET_REWARD, interval=interval):
                logger.info(f'{GET_REWARD} -> {click_button}')
                self.device.click(click_button)
                return True

        return False

    def handle_battle_pass_notification(self, interval=5) -> bool:
        """
        Popup notification that you enter battle pass the first time.

        Args:
            interval:

        Returns:
            If handled.
        """
        if self.appear_then_click(BATTLE_PASS_NOTIFICATION, interval=interval):
            return True

        return False

    def handle_monthly_card_reward(self, interval=1) -> bool:
        """
        Popup at 04:00 server time if you have purchased the monthly card.

        Args:
            interval:

        Returns:
            If handled.
        """
        if self.appear_then_click(MONTHLY_CARD_REWARD, interval=interval):
            return True
        if self.appear_then_click(MONTHLY_CARD_GET_ITEM, interval=interval):
            return True

        return False

    def handle_popup_cancel(self, interval=2) -> bool:
        """
        Args:
            interval:

        Returns:
            If handled.
        """
        if self.appear_then_click(POPUP_CANCEL, interval=interval):
            return True

        return False

    def handle_popup_confirm(self, interval=2) -> bool:
        """
        Args:
            interval:

        Returns:
            If handled.
        """
        if self.appear_then_click(POPUP_CONFIRM, interval=interval):
            return True

        return False

    def handle_popup_single(self, interval=2) -> bool:
        """
        Popup with one single confirm button in the middle.

        Args:
            interval:

        Returns:
            If handled.
        """
        if self.appear_then_click(POPUP_SINGLE, interval=interval):
            return True

        return False

    def handle_get_light_cone(self, interval=2) -> bool:
        """
        Popup when getting a light cone from Echo of War.

        Args:
            interval:

        Returns:
            If handled.
        """
        if self.appear(GET_LIGHT_CONE, interval=interval):
            logger.info(f'{GET_LIGHT_CONE} -> {GET_REWARD}')
            self.device.click(GET_REWARD)
            return True

        return False

    def handle_get_character(self, interval=2) -> bool:
        """
        Popup when getting a character from rogue rewards.

        Args:
            interval:

        Returns:
            If handled.
        """
        if self.appear(GET_CHARACTER, interval=interval):
            logger.info(f'{GET_CHARACTER} -> {GET_REWARD}')
            self.device.click(GET_REWARD)
            return True

        return False

    def handle_ui_close(self, appear_button: ButtonWrapper | Callable, interval=2) -> bool:
        """
        Args:
            appear_button: Click if button appears
            interval:

        Returns:
            If handled.
        """
        if callable(appear_button):
            if self.interval_is_reached(appear_button, interval=interval) and appear_button():
                logger.info(f'{appear_button.__name__} -> {CLOSE}')
                self.device.click(CLOSE)
                self.interval_reset(appear_button, interval=interval)
                return True
        else:
            if self.appear(appear_button, interval=interval):
                logger.info(f'{appear_button} -> {CLOSE}')
                self.device.click(CLOSE)
                return True

        return False

    def handle_ui_back(self, appear_button: ButtonWrapper | Callable, interval=2) -> bool:
        """
        Args:
            appear_button: Click if button appears
            interval:

        Returns:
            If handled.
        """
        if callable(appear_button):
            if self.interval_is_reached(appear_button, interval=interval) and appear_button():
                logger.info(f'{appear_button.__name__} -> {BACK}')
                self.device.click(BACK)
                self.interval_reset(appear_button, interval=interval)
                return True
        else:
            if self.appear(appear_button, interval=interval):
                logger.info(f'{appear_button} -> {BACK}')
                self.device.click(BACK)
                return True

        return False
