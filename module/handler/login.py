from datetime import datetime

from module.base.timer import Timer
from module.combat.combat import Combat
from module.handler.assets import *
from module.logger import logger
from module.ui.ui import MAIN_CHECK, EVENT_LIST_CHECK, BACK_ARROW


class LoginHandler(Combat):
    def handle_app_login(self):
        logger.hr('App login')

        confirm_timer = Timer(1.5, count=4).start()
        login_success = False
        while 1:
            self.device.screenshot()

            if self.handle_get_items(save_get_items=False):
                continue
            if self.handle_get_ship():
                continue
            if self.appear_then_click(LOGIN_ANNOUNCE, offset=(30, 30), interval=5):
                continue
            if self.appear(EVENT_LIST_CHECK, offset=(30, 30), interval=5):
                self.device.click(BACK_ARROW)
                continue
            if self.appear_then_click(LOGIN_GAME_UPDATE, offset=(30, 30), interval=5):
                continue
            if self.appear_then_click(LOGIN_RETURN_SIGN, offset=(30, 30), interval=5):
                continue
            if self.appear_then_click(LOGIN_CONFIRM, interval=5):
                continue

            if self.info_bar_count() and self.appear_then_click(LOGIN_CHECK, interval=5):
                if not login_success:
                    logger.info('Login success')
                    login_success = True
            if self.appear(MAIN_CHECK):
                if confirm_timer.reached():
                    logger.info('Login to main confirm')
                    break
            else:
                confirm_timer.reset()

        return True

    def app_restart(self):
        logger.hr('App restart')
        self.device.app_stop()
        self.device.app_start()
        self.handle_app_login()
        self.config.start_time = datetime.now()

    def app_ensure_start(self):
        if not self.device.app_is_running():
            self.device.app_start()
            self.handle_app_login()
            return True

        return False
