from module.base.button import ButtonWrapper
from module.base.decorator import run_once
from module.base.timer import Timer
from module.exception import GameNotRunningError, GamePageUnknownError
from module.logger import logger
from module.ocr.ocr import Ocr
from tasks.base.assets.assets_base_page import MAP_EXIT
from tasks.base.main_page import MainPage
from tasks.base.page import Page, page_main
from tasks.combat.assets.assets_combat_finish import COMBAT_EXIT
from tasks.combat.assets.assets_combat_interact import MAP_LOADING
from tasks.combat.assets.assets_combat_prepare import COMBAT_PREPARE
from tasks.daily.assets.assets_daily_trial import INFO_CLOSE
from tasks.login.assets.assets_login import LOGIN_CONFIRM


class UI(MainPage):
    ui_current: Page
    ui_main_confirm_timer = Timer(0.2, count=0)

    def ui_page_appear(self, page):
        """
        Args:
            page (Page):
        """
        return self.appear(page.check_button)

    def ui_get_current_page(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Returns:
            Page:

        Raises:
            GameNotRunningError:
            GamePageUnknownError:
        """
        logger.info("UI get current page")

        @run_once
        def app_check():
            if not self.device.app_is_running():
                raise GameNotRunningError("Game not running")

        @run_once
        def minicap_check():
            if self.config.Emulator_ControlMethod == "uiautomator2":
                self.device.uninstall_minicap()

        @run_once
        def rotation_check():
            self.device.get_orientation()

        timeout = Timer(10, count=20).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
                if not hasattr(self.device, "image") or self.device.image is None:
                    self.device.screenshot()
            else:
                self.device.screenshot()

            # End
            if timeout.reached():
                break

            # Known pages
            for page in Page.iter_pages():
                if page.check_button is None:
                    continue
                if self.ui_page_appear(page=page):
                    logger.attr("UI", page.name)
                    self.ui_current = page
                    return page

            # Unknown page but able to handle
            logger.info("Unknown ui page")
            if self.ui_additional():
                timeout.reset()
                continue
            if self.handle_popup_single():
                timeout.reset()
                continue
            if self.handle_popup_confirm():
                timeout.reset()
                continue
            if self.appear_then_click(LOGIN_CONFIRM, interval=5):
                timeout.reset()
                continue
            if self.appear(MAP_LOADING, interval=5):
                logger.info('Map loading')
                timeout.reset()
                continue

            app_check()
            minicap_check()
            rotation_check()

        # Unknown page, need manual switching
        logger.warning("Unknown ui page")
        logger.attr("EMULATOR__SCREENSHOT_METHOD", self.config.Emulator_ScreenshotMethod)
        logger.attr("EMULATOR__CONTROL_METHOD", self.config.Emulator_ControlMethod)
        logger.attr("Lang", self.config.LANG)
        logger.warning("Starting from current page is not supported")
        logger.warning(f"Supported page: {[str(page) for page in Page.iter_pages()]}")
        logger.warning('Supported page: Any page with a "HOME" button on the upper-right')
        logger.critical("Please switch to a supported page before starting SRC")
        raise GamePageUnknownError

    def ui_goto(self, destination, skip_first_screenshot=True):
        """
        Args:
            destination (Page):
            skip_first_screenshot:
        """
        # Create connection
        Page.init_connection(destination)
        self.interval_clear(list(Page.iter_check_buttons()))

        logger.hr(f"UI goto {destination}")
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Destination page
            if self.ui_page_appear(destination):
                logger.info(f'Page arrive: {destination}')
                if self.ui_page_confirm(destination):
                    logger.info(f'Page arrive confirm {destination}')
                break

            # Other pages
            clicked = False
            for page in Page.iter_pages():
                if page.parent is None or page.check_button is None:
                    continue
                if self.appear(page.check_button, interval=5):
                    logger.info(f'Page switch: {page} -> {page.parent}')
                    self.handle_lang_check(page)
                    if self.ui_page_confirm(page):
                        logger.info(f'Page arrive confirm {page}')
                    button = page.links[page.parent]
                    self.device.click(button)
                    self.ui_button_interval_reset(button)
                    clicked = True
                    break
            if clicked:
                continue

            # Additional
            if self.ui_additional():
                continue
            if self.handle_popup_single():
                continue
            if self.handle_popup_confirm():
                continue
            if self.appear_then_click(LOGIN_CONFIRM, interval=5):
                continue

        # Reset connection
        Page.clear_connection()

    def ui_ensure(self, destination, acquire_lang_checked=True, skip_first_screenshot=True):
        """
        Args:
            destination (Page):
            acquire_lang_checked:
            skip_first_screenshot:

        Returns:
            bool: If UI switched.
        """
        logger.hr("UI ensure")
        self.ui_get_current_page(skip_first_screenshot=skip_first_screenshot)

        self.ui_leave_special()

        if acquire_lang_checked:
            if self.acquire_lang_checked():
                self.ui_get_current_page(skip_first_screenshot=skip_first_screenshot)

        if self.ui_current == destination:
            logger.info("Already at %s" % destination)
            return False
        else:
            logger.info("Goto %s" % destination)
            self.ui_goto(destination, skip_first_screenshot=True)
            return True

    def ui_ensure_index(
            self,
            index,
            letter,
            next_button,
            prev_button,
            skip_first_screenshot=False,
            fast=True,
            interval=(0.2, 0.3),
    ):
        """
        Args:
            index (int):
            letter (Ocr, callable): OCR button.
            next_button (Button):
            prev_button (Button):
            skip_first_screenshot (bool):
            fast (bool): Default true. False when index is not continuous.
            interval (tuple, int, float): Seconds between two click.
        """
        logger.hr("UI ensure index")
        retry = Timer(1, count=2)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if isinstance(letter, Ocr):
                current = letter.ocr_single_line(self.device.image)
            else:
                current = letter(self.device.image)

            logger.attr("Index", current)
            diff = index - current
            if diff == 0:
                break
            if current == 0:
                logger.warning(f'ui_ensure_index got an empty current value: {current}')
                continue

            if retry.reached():
                button = next_button if diff > 0 else prev_button
                if fast:
                    self.device.multi_click(button, n=abs(diff), interval=interval)
                else:
                    self.device.click(button)
                retry.reset()

    def ui_click(
            self,
            click_button,
            check_button,
            appear_button=None,
            additional=None,
            retry_wait=5,
            skip_first_screenshot=True,
    ):
        """
        Args:
            click_button (ButtonWrapper):
            check_button (ButtonWrapper, callable, list[ButtonWrapper], tuple[ButtonWrapper]):
            appear_button (ButtonWrapper, callable, list[ButtonWrapper], tuple[ButtonWrapper]):
            additional (callable):
            retry_wait (int, float):
            skip_first_screenshot (bool):
        """
        if appear_button is None:
            appear_button = click_button
        logger.info(f'UI click: {appear_button} -> {check_button}')

        def process_appear(button):
            if isinstance(button, ButtonWrapper):
                return self.appear(button)
            elif callable(button):
                return button()
            elif isinstance(button, (list, tuple)):
                for b in button:
                    if self.appear(b):
                        return True
                return False
            else:
                return self.appear(button)

        click_timer = Timer(retry_wait, count=retry_wait // 0.5)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if process_appear(check_button):
                break

            # Click
            if click_timer.reached():
                if process_appear(appear_button):
                    self.device.click(click_button)
                    click_timer.reset()
                    continue
            if additional is not None:
                if additional():
                    continue

    def is_in_main(self):
        if self.appear(page_main.check_button):
            if self.image_color_count(page_main.check_button, color=(235, 235, 235), threshold=234, count=400):
                return True
        if self.appear(MAP_EXIT):
            if self.image_color_count(MAP_EXIT, color=(235, 235, 235), threshold=221, count=50):
                return True
        return False

    def ui_goto_main(self):
        return self.ui_ensure(destination=page_main)

    def ui_additional(self) -> bool:
        """
        Handle all possible popups during UI switching.

        Returns:
            If handled any popup.
        """
        if self.handle_reward():
            return True
        if self.handle_battle_pass_notification():
            return True
        if self.handle_monthly_card_reward():
            return True
        if self.handle_get_light_cone():
            return True
        if self.handle_ui_close(COMBAT_PREPARE, interval=5):
            return True
        if self.appear_then_click(COMBAT_EXIT, interval=5):
            return True
        if self.appear_then_click(INFO_CLOSE, interval=5):
            return True

        return False

    def _ui_button_confirm(
            self,
            button,
            confirm=Timer(0.1, count=0),
            timeout=Timer(2, count=6),
            skip_first_screenshot=True
    ):
        confirm.reset()
        timeout.reset()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning(f'_ui_button_confirm({button}) timeout')
                break

            if self.appear(button):
                if confirm.reached():
                    break
            else:
                confirm.reset()

    def ui_page_confirm(self, page):
        """
        Args:
            page (Page):

        Returns:
            bool: If handled
        """
        if page == page_main:
            self._ui_button_confirm(page.check_button)
            return True

        return False

    def ui_button_interval_reset(self, button):
        """
        Reset interval of some button to avoid mistaken clicks

        Args:
            button (Button):
        """
        pass
