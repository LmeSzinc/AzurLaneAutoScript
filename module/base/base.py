from module.base.button import Button
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import *
from module.combat.emotion import Emotion
from module.config.config import AzurLaneConfig
from module.config.server import set_server, to_package
from module.device.device import Device
from module.device.method.utils import HierarchyButton
from module.logger import logger
from module.map_detection.utils import fit_points
from module.statistics.azurstats import AzurStats


class ModuleBase:
    config: AzurLaneConfig
    device: Device

    def __init__(self, config, device=None, task=None):
        """
        Args:
            config (AzurLaneConfig, str): Name of the user config under ./config
            device (Device): To reuse a device. If None, create a new Device object.
            task (str): Bind a task only for dev purpose. Usually to be None for auto task scheduling.
        """
        if isinstance(config, str):
            self.config = AzurLaneConfig(config, task=task)
        else:
            self.config = config
        if device is not None:
            self.device = device
        else:
            self.device = Device(config=self.config)
        self.interval_timer = {}

    @cached_property
    def stat(self) -> AzurStats:
        return AzurStats(config=self.config)

    @cached_property
    def emotion(self) -> Emotion:
        return Emotion(config=self.config)

    def ensure_button(self, button):
        if isinstance(button, str):
            button = HierarchyButton(self.device.hierarchy, button)

        return button

    def appear(self, button, offset=0, interval=0, threshold=None):
        """
        Args:
            button (Button, Template, HierarchyButton, str):
            offset (bool, int):
            interval (int, float): interval between two active events.
            threshold (int, float): 0 to 1 if use offset, bigger means more similar,
                0 to 255 if not use offset, smaller means more similar

        Returns:
            bool:

        Examples:
            Image detection:
            ```
            self.device.screenshot()
            self.appear(Button(area=(...), color=(...), button=(...))
            self.appear(Template(file='...')
            ```

            Hierarchy detection (detect elements with xpath):
            ```
            self.device.dump_hierarchy()
            self.appear('//*[@resource-id="..."]')
            ```
        """
        button = self.ensure_button(button)
        self.device.stuck_record_add(button)

        if interval:
            if button.name in self.interval_timer:
                if self.interval_timer[button.name].limit != interval:
                    self.interval_timer[button.name] = Timer(interval)
            else:
                self.interval_timer[button.name] = Timer(interval)
            if not self.interval_timer[button.name].reached():
                return False

        if isinstance(button, HierarchyButton):
            appear = bool(button)
        elif offset:
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

    def appear_then_click(self, button, screenshot=False, genre='items', offset=0, interval=0, threshold=None):
        button = self.ensure_button(button)
        appear = self.appear(button, offset=offset, interval=interval, threshold=threshold)
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

    def wait_until_stable(self, button, timer=Timer(0.3, count=1), timeout=Timer(5, count=10), skip_first_screenshot=True):
        button._match_init = False
        timeout.reset()
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

            if timeout.reached():
                logger.warning(f'wait_until_stable({button}) timeout')
                break

    def image_crop(self, button):
        """Extract the area from image.

        Args:
            button(Button, tuple): Button instance or area tuple.
        """
        if isinstance(button, Button):
            return crop(self.device.image, button.area)
        else:
            return crop(self.device.image, button)

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
        image = self.image_crop(button)
        mask = color_similarity_2d(image, color=color) > threshold
        return np.sum(mask) > count

    def image_color_button(self, area, color, color_threshold=250, encourage=5, name='COLOR_BUTTON'):
        """
        Find an area with pure color on image, convert into a Button.

        Args:
            area (tuple[int]): Area to search from
            color (tuple[int]): Target color
            color_threshold (int): 0-255, 255 means exact match
            encourage (int): Radius of button
            name (str): Name of the button

        Returns:
            Button: Or None if nothing matched.
        """
        image = color_similarity_2d(self.image_crop(area), color=color)
        points = np.array(np.where(image > color_threshold)).T[:, ::-1]
        if points.shape[0] < encourage ** 2:
            # Not having enough pixels to match
            return None

        point = fit_points(points, mod=image_size(image), encourage=encourage)
        point = ensure_int(point + area[:2])
        button_area = area_offset((-encourage, -encourage, encourage, encourage), offset=point)
        color = get_color(self.device.image, button_area)
        return Button(area=button_area, color=color, button=button_area, name=name)

    def interval_reset(self, button):
        if isinstance(button, (list, tuple)):
            for b in button:
                self.interval_reset(b)
        else:
            if button.name in self.interval_timer:
                self.interval_timer[button.name].reset()

    def interval_clear(self, button):
        if isinstance(button, (list, tuple)):
            for b in button:
                self.interval_clear(b)
        else:
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
        if isinstance(value, Image.Image):
            value = np.array(value)
        elif isinstance(value, str):
            value = load_image(value)

        self.device.image = value

    def set_server(self, server):
        """
        For development.
        Change server and this will effect globally,
        including assets and server specific methods.
        """
        package = to_package(server)
        self.device.package = package
        set_server(server)
        logger.attr('Server', self.config.SERVER)
