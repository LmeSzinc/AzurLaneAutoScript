from PIL import Image

from module.base.button import Button
from module.base.timer import Timer
from module.base.utils import *
from module.config.config import AzurLaneConfig
from module.device.device import Device


class ModuleBase:
    config: AzurLaneConfig
    device: Device

    def __init__(self, config, device=None):
        """
        Args:
            config (AzurLaneConfig, str):
            device (Device):
        """
        if isinstance(config, str):
            self.config = AzurLaneConfig(config)
        else:
            self.config = config
        if device is not None:
            self.device = device
        else:
            self.device = Device(config=self.config)

        self.interval_timer = {}

    def appear(self, button, offset=0, interval=0, threshold=None):
        """
        Args:
            button (Button, Template):
            offset (bool, int):
            interval (int, float): interval between two active events.
            threshold (int, float): 0 to 1 if use offset, bigger means more similar,
                0 to 255 if not use offset, smaller means more similar

        Returns:
            bool:
        """
        self.device.stuck_record_add(button)

        if interval:
            if button.name not in self.interval_timer:
                self.interval_timer[button.name] = Timer(interval)
            if not self.interval_timer[button.name].reached():
                return False

        if offset:
            if isinstance(offset, bool):
                offset = self.config.BUTTON_OFFSET
            appear = button.match(self.device.image, offset=offset,
                                  threshold=self.config.BUTTON_MATCH_SIMILARITY if threshold is None else threshold)
        else:
            appear = button.appear_on(self.device.image,
                                      threshold=self.config.COLOR_SIMILAR_THRESHOLD if threshold is None else threshold)

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

    def wait_until_stable(self, button, timer=Timer(0.3, count=1), skip_first_screenshot=True):
        button._match_init = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if button._match_init:
                if button.match(self.device.image, offset=(0, 0)):
                    if timer.reached():
                        break
                else:
                    button.load_color(self.device.image)
                    timer.reset()
            else:
                button.load_color(self.device.image)
                button._match_init = True

    def image_area(self, button):
        """Extract the area from image.

        Args:
            button(Button, tuple): Button instance or area tuple.
        """
        if isinstance(button, Button):
            return self.device.image.crop(button.area)
        else:
            return self.device.image.crop(button)

    def image_color_count(self, button, color, threshold=221, count=50):
        """
        Args:
            button (Button, tuple): Button instance or area.
            color (tuple): RGB.
            threshold: 255 means colors are the same, the lower the worse.
            count (int): Pixels count.

        Returns:
            bool:
        """
        if isinstance(button, Button):
            image = self.device.image.crop(button.area)
        else:
            image = self.device.image.crop(button)
        mask = color_similarity_2d(image, color=color) > threshold
        return np.sum(mask) > count

    def interval_reset(self, button):
        if button.name in self.interval_timer:
            self.interval_timer[button.name].reset()

    def interval_clear(self, button):
        if button.name in self.interval_timer:
            self.interval_timer[button.name].clear()

    _image_file = ''

    @property
    def image_file(self):
        return self._image_file

    @image_file.setter
    def image_file(self, value):
        """
        For development.
        Load image from local file system and set it to self.device.image
        Test an image without taking a screenshot from emulator.
        """
        if isinstance(value, np.ndarray):
            value = Image.fromarray(value)
        elif isinstance(value, str):
            value = Image.open(value).convert('RGB')

        self.device.image = value
