
import module.config.server as server
from module.base.timer import Timer
from module.handler.assets import *  # noqa: F403  (data-bundle star import)
from module.logger import logger
from module.map.assets import *  # noqa: F403  (data-bundle star import)
from module.ui.assets import *  # noqa: F403  (data-bundle star import)
from module.ui.ui import UI


class LoginHandler(UI):
    def _handle_app_login(self):
        """
        Pages:
            in: Any page
            out: page_main

        Raises:
            GameStuckError:
            GameTooManyClickError:
            GameNotRunningError:
        """
        logger.hr("App login")

        confirm_timer = Timer(1.5, count=4).start()
        orientation_timer = Timer(5)
        login_success = False
        self.device.stuck_record_clear()
        self.device.click_record_clear()

        while 1:
            # Watch device rotation
            if not login_success and orientation_timer.reached():
                # Screen may rotate after starting an app
                self.device.get_orientation()
                orientation_timer.reset()

            self.device.screenshot()

            # End
            if self.is_in_main():
                if confirm_timer.reached():
                    logger.info("Login to main confirm")
                    break
            else:
                confirm_timer.reset()

            # Login
            if self.match_template_color(LOGIN_CHECK, offset=(30, 30), interval=5):
                self.device.click(LOGIN_CHECK)
                if not login_success:
                    logger.info("Login success")
                    login_success = True
            if self.appear(ANDROID_NO_RESPOND, offset=(30, 30), interval=5):
                logger.warning("Emulator no respond")
                self.device.click_record_add(ANDROID_NO_RESPOND)
                self.device.click_record_check()
                self.device.click(ANDROID_NO_RESPOND, control_check=False)
                continue
            if self.appear_then_click(LOGIN_ANNOUNCE, offset=(30, 30), interval=5):
                continue
            if self.appear_then_click(LOGIN_ANNOUNCE_2, offset=(30, 30), interval=5):
                continue
            if self.appear(EVENT_LIST_CHECK, offset=(30, 30), interval=5):
                self.device.click(BACK_ARROW)
                continue
            # Updates and maintenance
            if self.appear_then_click(MAINTENANCE_ANNOUNCE, offset=(30, 30), interval=5):
                continue
            if self.appear_then_click(LOGIN_GAME_UPDATE, offset=(30, 30), interval=5):
                continue
            if server.server == "cn" and not login_success:
                if self.handle_cn_user_agreement():
                    continue
            # Player return
            if self.appear_then_click(LOGIN_RETURN_SIGN, offset=(30, 30), interval=5):
                continue
            if self.appear_then_click(LOGIN_RETURN_INFO, offset=(30, 30), interval=5):
                continue
            if self.appear_then_click(AVATAR_EXPIRED, offset=(30, 30), interval=5):
                continue
            # Popups
            if self.handle_popup_confirm("LOGIN"):
                continue
            if self.handle_urgent_commission():
                continue
            # Popups appear at page_main
            if self.ui_page_main_popups(get_ship=login_success):
                return True
            # Always goto page_main
            if self.appear_then_click(GOTO_MAIN, offset=(30, 30), interval=5):
                continue

        return True

    _user_agreement_timer = Timer(1, count=2)

    def handle_cn_user_agreement(self):
        if not self._user_agreement_timer.reached():
            return False

        right = self.image_color_button(
            area=(640, 360, 1280, 720),
            color=(78, 189, 234),
            color_threshold=245,
            encourage=25,
            name="AGREEMENT_CONFIRM",
        )
        if right is None:
            return False
        # 2026.04.17 No scroll anymore, just bare swipe before clicking confirm
        # if having blue button at right half of screen, but missing in left, it's a confirm button
        # if having both, it's a blue button at middle confirming login
        left = self.image_color_button(
            area=(0, 360, 640, 720), color=(78, 189, 234), color_threshold=245, encourage=25, name="AGREEMENT_CONFIRM"
        )
        if left is None:
            # User agreement
            # just somewhere at the middle
            box = (350, 230, 920, 430)
            self.device.swipe_vector((0, -150), box, name="AGREEMENT_SCROLL")
            self.device.swipe_vector((0, -150), box, name="AGREEMENT_SCROLL")
            self.device.click(right)
            self._user_agreement_timer.reset()
            return True
        else:
            # User login
            self.device.click(right)
            self._user_agreement_timer.reset()
            return True

    def handle_app_login(self):
        """
        Returns:
            bool: If login success

        Raises:
            GameStuckError:
            GameTooManyClickError:
            GameNotRunningError:
        """
        logger.info("handle_app_login")
        self.device.screenshot_interval_set(1.0)
        try:
            self._handle_app_login()
        finally:
            self.device.screenshot_interval_set()

    def app_stop(self):
        logger.hr("App stop")
        self.device.app_stop()

    def app_start(self):
        logger.hr("App start")
        self.device.app_start()
        self.handle_app_login()

    def app_restart(self):
        logger.hr("App restart")
        self.device.app_stop()
        self.device.app_start()
        self.handle_app_login()
        self.config.task_delay(server_update=True)
