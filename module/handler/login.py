from datetime import datetime

import module.config.server as server
from module.base.timer import Timer
from module.combat.combat import Combat
from module.exception import GameTooManyClickError, ScriptError
from module.handler.assets import *
from module.logger import logger
from module.map.assets import *
from module.ui.assets import *
from module.ui.scroll import Scroll
from module.ui.ui import MAIN_CHECK

USER_AGREEMENT_SCROLL = Scroll(USER_AGREEMENT_SCROLL, color=(182, 189, 202), name='USER_AGREEMENT_SCROLL')


class LoginHandler(Combat):
    def _handle_app_login(self):
        """
        Pages:
            in: Any page
            out: page_main
        """
        logger.hr('App login')

        confirm_timer = Timer(1.5, count=4).start()
        login_success = False
        while 1:
            self.device.screenshot()

            if self.handle_get_items(save_get_items=False):
                continue
            if self.handle_get_ship():
                continue
            if self.handle_user_agreement():
                continue
            if self.appear_then_click(LOGIN_ANNOUNCE, offset=(30, 30), interval=5):
                continue
            if self.appear(EVENT_LIST_CHECK, offset=(30, 30), interval=5):
                self.device.click(BACK_ARROW)
                continue
            if self.appear_then_click(MAINTENANCE_ANNOUNCE, offset=(30, 30), interval=5):
                continue
            if self.appear_then_click(LOGIN_GAME_UPDATE, offset=(30, 30), interval=5):
                continue
            if self.appear_then_click(LOGIN_RETURN_SIGN, offset=(30, 30), interval=5):
                continue
            if self.appear_then_click(LOGIN_RETURN_INFO, offset=(30, 30), interval=5):
                continue
            if server.server == 'cn':
                if self.appear_then_click(LOGIN_CONFIRM, interval=5):
                    continue
            if self.handle_popup_confirm('LOGIN'):
                continue
            if self.handle_guild_popup_cancel():
                continue
            if self.handle_urgent_commission(save_get_items=False):
                continue
            if self.appear_then_click(GOTO_MAIN, offset=(30, 30), interval=5):
                continue

            if self.appear_then_click(LOGIN_CHECK, interval=5):
                if not login_success:
                    logger.info('Login success')
                    login_success = True
            if self.appear(MAIN_CHECK):
                if confirm_timer.reached():
                    logger.info('Login to main confirm')
                    break
            else:
                confirm_timer.reset()

        self.config.start_time = datetime.now()
        return True

    def handle_app_login(self):
        """
        Returns:
            bool: If login success

        Raises:
            ScriptError: If login failed more than 3
        """
        for _ in range(3):
            self.device.stuck_record_clear()
            try:
                self._handle_app_login()
                return True
            except GameTooManyClickError as e:
                logger.warning(e)
                self.device.app_stop()
                self.device.app_start()
                continue

        logger.warning('Login failed more than 3')
        self.device.send_notification('ScriptError', 'Login failed more than 3')
        raise ScriptError('Login failed more than 3')

    def app_restart(self):
        logger.hr('App restart')
        self.device.app_stop()
        self.device.app_start()
        self.handle_app_login()

    def app_ensure_start(self):
        if not self.device.app_is_running():
            self.device.app_start()
            self.handle_app_login()
            return True

        return False

    def ensure_no_unfinished_campaign(self, confirm_wait=3):
        """
        Pages:
            in: page_main
            out: page_main
        """
        def ensure_campaign_retreat():
            if self.appear_then_click(WITHDRAW, offset=(30, 30), interval=5):
                return True
            if self.handle_popup_confirm('WITHDRAW'):
                return True

        def in_campaign():
            return self.appear(CAMPAIGN_CHECK, offset=(30, 30)) \
                   or self.appear(CAMPAIGN_MENU_CHECK, offset=(30, 30)) \
                   or self.appear(EVENT_CHECK, offset=(30, 30)) \
                   or self.appear(SP_CHECK, offset=(30, 30))

        self.ui_click(MAIN_GOTO_CAMPAIGN, check_button=in_campaign, additional=ensure_campaign_retreat,
                      confirm_wait=confirm_wait, skip_first_screenshot=True)
        self.ui_goto_main()

    def handle_game_stuck(self):
        logger.warning(f'{self.config.PACKAGE_NAME} will be restart in 10 seconds')
        logger.warning('If you are playing by hand, please stop Alas')
        self.device.send_notification('Game stucked', 'will be restart in 10 seconds')
        self.device.sleep(10)

        self.app_restart()
        self.ensure_no_unfinished_campaign()

    def handle_user_agreement(self):
        """
        For CN only.
        CN client is bugged. User Agreement and Privacy Policy may popup again even you have agreed with it.
        This method scrolls to the bottom and click AGREE.

        Returns:
            bool: If handled.
        """
        if server.server == 'cn':
            if self.appear(USER_AGREEMENT_CONFIRM, interval=2):
                USER_AGREEMENT_SCROLL.set_bottom(main=self)
                self.device.click(USER_AGREEMENT_CONFIRM)
                return True

        return False
