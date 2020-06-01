from module.base.button import Button
from module.base.timer import Timer
from module.config.config import AzurLaneConfig
from module.device.device import Device


class ModuleBase:
    def __init__(self, config, device=None):
        """
        Args:
            config (AzurLaneConfig):
            device (Device):
        """
        self.config = config
        self.interval_timer = {}
        if device is not None:
            self.device = device
        else:
            self.device = Device(config=config)

    def appear(self, button, offset=0, interval=0):
        """
        Args:
            button (Button, Template):
            offset (bool, int):
            interval (int, float): interval between two active events.

        Returns:
            bool:
        """
        if interval:
            if button.name not in self.interval_timer:
                self.interval_timer[button.name] = Timer(interval)
            if not self.interval_timer[button.name].reached():
                return False

        if offset:
            if isinstance(offset, bool):
                offset = self.config.BUTTON_OFFSET
            appear = button.match(self.device.image, offset=offset, threshold=self.config.BUTTON_MATCH_SIMILARITY)
        else:
            appear = button.appear_on(self.device.image, threshold=self.config.COLOR_SIMILAR_THRESHOLD)

        if appear and interval:
            self.interval_timer[button.name].reset()

        return appear

    def appear_then_click(self, button, screenshot=False, genre='items', offset=0, interval=0):
        appear = self.appear(button, offset=offset, interval=interval)
        if appear:
            if screenshot:
                self.device.sleep(self.config.WAIT_BEFORE_SAVING_SCREEN_SHOT)
                self.device.screenshot()
                self.device.save_screenshot(genre=genre)
            self.device.click(button)
        return appear

    def wait_until_appear(self, button, offset=0, skip_first_screenshot=False):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.appear(button, offset=offset):
                break

    def wait_until_appear_then_click(self, button, offset=0):
        self.wait_until_appear(button, offset=offset)
        self.device.click(button)

    def wait_until_disappear(self, button, offset=0):
        while 1:
            self.device.screenshot()
            if not self.appear(button, offset=offset):
                break

    def image_area(self, button):
        """Extract the area from image.

        Args:
            button(Button): Button instance.

        Returns:
            PIL.Image.Image:
        """
        return self.device.image.crop(button.area)

    def interval_reset(self, button):
        if button.name in self.interval_timer:
            self.interval_timer[button.name].reset()
