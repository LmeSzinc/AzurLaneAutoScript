from module.combat.combat import Combat
from module.logger import logger
from module.base.timer import Timer
from module.handler.assets import LOGIN_CHECK, LOGIN_ANNOUNCE
from module.ui.ui import MAIN_CHECK, EVENT_LIST_CHECK, BACK_ARROW


class LoginHandler(Combat):
    def handle_app_login(self):
        logger.hr('App login')

        confirm_timer = Timer(2)
        while 1:
            self.device.screenshot()

            if self.handle_get_items(save_get_items=False):
                continue
            if self.handle_get_ship():
                continue
            if self.appear_then_click(LOGIN_ANNOUNCE, offset=(30, 30), interval=1):
                continue
            if self.appear(EVENT_LIST_CHECK, offset=(30, 30), interval=1):
                self.device.click(BACK_ARROW)
                continue

            if self.info_bar_count() and self.appear_then_click(LOGIN_CHECK, interval=0.5):
                logger.info('Login success')
            if self.appear(MAIN_CHECK):
                confirm_timer.start()

            if confirm_timer.started() and confirm_timer.reached():
                logger.info('Login to main confirm')
                break

        return True

    def app_restart(self):
        logger.hr('App restart')
        self.device.app_stop()
        self.device.app_start()
        self.handle_app_login()

    def app_ensure_start(self):
        if not self.device.app_is_running():
            self.device.app_start()
            self.handle_app_login()
