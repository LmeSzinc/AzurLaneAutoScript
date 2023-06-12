from module.logger import logger
from tasks.base.assets.assets_base_page import CLOSE
from tasks.base.page import page_camera
from tasks.base.ui import UI
from tasks.daily.assets.assets_daily import *


class CameraUI(UI):
    def take_picture(self, skip_first_screenshot=True):
        """
        Examples:
            self = CameraUI('alas')
            self.device.screenshot()
            self.take_picture()

        Pages:
            in: Any
            out: page_camera, TAKE_PICTURE
        """
        self.ui_ensure(page_camera, skip_first_screenshot)
        # Take picture
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.appear_then_click(TAKE_PICTURE):
                logger.info('Taking picture')
                continue
            if self.appear(PICTURE_TAKEN):
                logger.info('Picture was taken')
                break
        # Quit from the picture ui
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.appear(TAKE_PICTURE):
                logger.info('Back to camera main page')
                break
            if self.appear_then_click(CLOSE):
                logger.info('Photo page was exited')
                continue
