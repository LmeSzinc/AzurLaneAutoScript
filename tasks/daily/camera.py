from module.logger import logger
from tasks.base.page import page_camera
from tasks.base.ui import UI
from tasks.daily.assets.assets_daily_camera import PICTURE_TAKEN, TAKE_PICTURE


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
        logger.hr('Take picture', level=2)
        self.ui_ensure(page_camera, skip_first_screenshot)
        # Take picture
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.appear_then_click(TAKE_PICTURE, interval=1):
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
            if self.is_in_main():
                logger.info('Back to camera main page')
                break
            if self.handle_ui_close(PICTURE_TAKEN, interval=1):
                continue
            if self.handle_ui_close(TAKE_PICTURE, interval=1):
                continue
