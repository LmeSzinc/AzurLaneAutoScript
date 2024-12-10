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
from module.webui.setting import cached_class_property


class ModuleBase:
    config: AzurLaneConfig
    device: Device

    EARLY_OCR_IMPORT = False

    def __init__(self, config, device=None, task=None):
        """
        Args:
            config (AzurLaneConfig, str):
                Name of the user config under ./config
            device (Device, str):
                To reuse a device.
                If None, create a new Device object.
                If str, create a new Device object and use the given device as serial.
            task (str):
                Bind a task only for dev purpose. Usually to be None for auto task scheduling.
                If None, use default configs.
        """
        if isinstance(config, AzurLaneConfig):
            self.config = config
            if task is not None:
                self.config.init_task(task)
        elif isinstance(config, str):
            self.config = AzurLaneConfig(config, task=task)
        else:
            logger.warning('Alas ModuleBase received an unknown config, assume it is AzurLaneConfig')
            self.config = config

        if isinstance(device, Device):
            self.device = device
        elif device is None:
            self.device = Device(config=self.config)
        elif isinstance(device, str):
            self.config.override(Emulator_Serial=device)
            self.device = Device(config=self.config)
        else:
            logger.warning('Alas ModuleBase received an unknown device, assume it is Device')
            self.device = device

        self.interval_timer = {}
        self.early_ocr_import()

    @cached_property
    def stat(self) -> AzurStats:
        return AzurStats(config=self.config)

    @cached_property
    def emotion(self) -> Emotion:
        return Emotion(config=self.config)

    def early_ocr_import(self):
        """
        Start a thread to import cnocr and mxnet while the Alas instance just starting to take screenshots
        The import is paralleled since taking screenshot is I/O-bound while importing is CPU-bound,
        thus would speed up the startup 0.5 ~ 1.0s and even 5s on slow PCs.
        """
        if ModuleBase.EARLY_OCR_IMPORT:
            return
        if not self.config.is_actual_task:
            logger.info('No actual task bound, skip early_ocr_import')
            return
        if self.config.task.command in ['Daemon', 'OpsiDaemon']:
            logger.info('No ocr in daemon task, skip early_ocr_import')
            return

        def do_ocr_import():
            # Wait first image
            import time
            while 1:
                if self.device.has_cached_image:
                    break
                time.sleep(0.01)

            logger.info('early_ocr_import start')
            from module.ocr.al_ocr import AlOcr
            _ = AlOcr
            logger.info('early_ocr_import finish')

        logger.info('early_ocr_import call')
        import threading
        thread = threading.Thread(target=do_ocr_import, daemon=True)
        thread.start()
        ModuleBase.EARLY_OCR_IMPORT = True

    @cached_class_property
    def worker(self):
        """
        A thread pool to run things at background

        Examples:
        ```
        def func(image):
            logger.info('Update thread start')
            with self.config.multi_set():
                self.dungeon_get_simuni_point(image)
                self.dungeon_update_stamina(image)
        ModuleBase.worker.submit(func, self.device.image)
        ```
        """
        logger.hr('Creating worker')
        from concurrent.futures import ThreadPoolExecutor
        pool = ThreadPoolExecutor(1)
        return pool

    def ensure_button(self, button):
        if isinstance(button, str):
            button = HierarchyButton(self.device.hierarchy, button)

        return button

    def appear(self, button, offset=0, interval=0, similarity=0.85, threshold=30):
        """
        Args:
            button (Button, Template, HierarchyButton, str):
            offset (bool, int):
            interval (int, float): interval between two active events.
            similarity (int, float): 0 to 1.
            threshold (int, float): 0 to 255 if not use offset, smaller means more similar

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
            appear = button.match(self.device.image, offset=offset, similarity=similarity)
        else:
            appear = button.appear_on(self.device.image, threshold=threshold)

        if appear and interval:
            self.interval_timer[button.name].reset()

        return appear

    def match_template_color(self, button, offset=(20, 20), interval=0, similarity=0.85, threshold=30):
        """
        Args:
            button (Button):
            offset (bool, int):
            interval (int, float): interval between two active events.
            similarity (int, float): 0 to 1.
            threshold (int, float): 0 to 255 if not use offset, smaller means more similar

        Returns:
            bool:
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

        appear = button.match_template_color(
            self.device.image, offset=offset, similarity=similarity, threshold=threshold)

        if appear and interval:
            self.interval_timer[button.name].reset()

        return appear

    def appear_then_click(self, button, screenshot=False, genre='items', offset=0, interval=0, similarity=0.85,
                          threshold=30):
        button = self.ensure_button(button)
        appear = self.appear(button, offset=offset, interval=interval, similarity=similarity, threshold=threshold)
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

    def image_crop(self, button, copy=True):
        """Extract the area from image.

        Args:
            button(Button, tuple): Button instance or area tuple.
            copy:
        """
        if isinstance(button, Button):
            return crop(self.device.image, button.area, copy=copy)
        elif hasattr(button, 'area'):
            return crop(self.device.image, button.area, copy=copy)
        else:
            return crop(self.device.image, button, copy=copy)

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
        if isinstance(button, np.ndarray):
            image = button
        else:
            image = self.image_crop(button, copy=False)
        mask = color_similarity_2d(image, color=color)
        cv2.inRange(mask, threshold, 255, dst=mask)
        sum_ = cv2.countNonZero(mask)
        return sum_ > count

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
        image = color_similarity_2d(self.image_crop(area, copy=False), color=color)
        points = np.array(np.where(image > color_threshold)).T[:, ::-1]
        if points.shape[0] < encourage ** 2:
            # Not having enough pixels to match
            return None

        point = fit_points(points, mod=image_size(image), encourage=encourage)
        point = ensure_int(point + area[:2])
        button_area = area_offset((-encourage, -encourage, encourage, encourage), offset=point)
        color = get_color(self.device.image, button_area)
        return Button(area=button_area, color=color, button=button_area, name=name)

    def get_interval_timer(self, button, interval=5, renew=False) -> Timer:
        if hasattr(button, 'name'):
            name = button.name
        elif callable(button):
            name = button.__name__
        else:
            name = str(button)

        try:
            timer = self.interval_timer[name]
            if renew and timer.limit != interval:
                timer = Timer(interval)
                self.interval_timer[name] = timer
            return timer
        except KeyError:
            timer = Timer(interval)
            self.interval_timer[name] = timer
            return timer

    def interval_reset(self, button, interval=3):
        if isinstance(button, (list, tuple)):
            for b in button:
                self.interval_reset(b)
            return

        if button is not None:
            if button.name in self.interval_timer:
                self.interval_timer[button.name].reset()
            else:
                self.interval_timer[button.name] = Timer(interval).reset()

    def interval_clear(self, button, interval=3):
        if isinstance(button, (list, tuple)):
            for b in button:
                self.interval_clear(b)
            return

        if button is not None:
            if button.name in self.interval_timer:
                self.interval_timer[button.name].clear()
            else:
                self.interval_timer[button.name] = Timer(interval).clear()

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
