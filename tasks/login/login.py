from module.base.timer import Timer
from module.exception import GameNotRunningError
from module.logger import logger
from tasks.base.page import page_main
from tasks.base.ui import UI
from tasks.login.assets.assets_login import LOGIN_CONFIRM, USER_AGREEMENT_ACCEPT, LOGIN_LOADING


class Login(UI):
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
        logger.hr('App login')
        orientation_timer = Timer(5)
        startup_timer = Timer(5).start()
        app_timer = Timer(5).start()
        login_success = False

        while 1:
            # Watch if game alive
            if app_timer.reached():
                if not self.device.app_is_running():
                    logger.error('Game died during launch')
                    raise GameNotRunningError('Game not running')
                app_timer.reset()
            # Watch device rotation
            if not login_success and orientation_timer.reached():
                # Screen may rotate after starting an app
                self.device.get_orientation()
                orientation_timer.reset()

            self.device.screenshot()

            # End
            # Game client requires at least 5s to start
            # The first few frames might be captured before app_stop(), ignore them
            if startup_timer.reached():
                if self.ui_page_appear(page_main):
                    logger.info('Login to main confirm')
                    break

            # Watch resource downloading and loading
            if self.appear(LOGIN_LOADING, interval=5):
                logger.info('Game resources downloading or loading')
                self.device.stuck_record_clear()

            # Login
            if self.appear_then_click(LOGIN_CONFIRM):
                login_success = True
                continue
            if self.appear_then_click(USER_AGREEMENT_ACCEPT):
                continue
            # Additional
            if self.handle_popup_single():
                continue
            if self.ui_additional():
                continue

        return True

    def handle_app_login(self):
        logger.info('handle_app_login')
        self.device.screenshot_interval_set(1.0)
        self.device.stuck_timer = Timer(300, count=300).start()
        try:
            self._handle_app_login()
        finally:
            self.device.screenshot_interval_set()
            self.device.stuck_timer = Timer(60, count=60).start()

    def app_stop(self):
        logger.hr('App stop')
        self.device.app_stop()

    def app_start(self):
        logger.hr('App start')
        self.device.app_start()
        self.handle_app_login()

    def app_restart(self):
        logger.hr('App restart')
        self.device.app_stop()
        self.device.app_start()
        self.handle_app_login()
        self.config.task_delay(server_update=True)
