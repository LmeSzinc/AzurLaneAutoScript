from module.logger import logger
from tasks.base.assets.assets_base_page import CLOSE
from tasks.base.page import page_camera, page_main
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
            if self.appear(page_main.check_button):
                logger.info('Back to camera main page')
                break
            if self.appear(PICTURE_TAKEN, interval=1):
                self.device.click(CLOSE)
                logger.info(f'{PICTURE_TAKEN} -> {CLOSE}')
                self.interval_reset(TAKE_PICTURE)
                continue
            if self.appear(TAKE_PICTURE, interval=1):
                self.device.click(CLOSE)
                logger.info(f'{TAKE_PICTURE} -> {CLOSE}')
                continue
