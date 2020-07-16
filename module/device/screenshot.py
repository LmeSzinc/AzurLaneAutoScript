import os
import time
from datetime import datetime
from io import BytesIO

import cv2
import lz4.block
import numpy as np
from PIL import Image
from retrying import retry

from module.base.timer import Timer
from module.device.connection import Connection
from module.logger import logger


class AscreencapError(Exception):
    pass


class Screenshot(Connection):
    _screenshot_method = 0
    _screenshot_method_fixed = False
    _bytepointer = 0

    _screenshot_interval_timer = Timer(0.1)
    _last_save_time = {}
    image: Image.Image

    def _screenshot_uiautomator2(self):
        image = self.device.screenshot()
        return image.convert('RGB')

    def _load_screenshot(self, screenshot):
        if self._screenshot_method == 0:
            return Image.open(BytesIO(screenshot)).convert('RGB')
        elif self._screenshot_method == 1:
            return Image.open(BytesIO(screenshot.replace(b'\r\n', b'\n'))).convert('RGB')
        elif self._screenshot_method == 2:
            return Image.open(BytesIO(screenshot.replace(b'\r\r\n', b'\n'))).convert('RGB')

    def _process_screenshot(self, screenshot):
        if self._screenshot_method_fixed:
            return self._load_screenshot(screenshot)
        else:
            for _ in range(3):
                try:
                    screenshot = self._load_screenshot(screenshot)
                except OSError:
                    self._screenshot_method += 1
                else:
                    self._screenshot_method_fixed = True
                    break
            return screenshot

    def _screenshot_adb(self):
        screenshot = self.adb_shell(['screencap', '-p'], serial=self.serial)
        return self._process_screenshot(screenshot)

    def _reposition_byte_pointer(self, byte_array):
        """Method to return the sanitized version of ascreencap stdout for devices
            that suffers from linker warnings. The correct pointer location will be saved
            for subsequent screen refreshes
        """
        while byte_array[self._bytepointer:self._bytepointer + 4] != b'BMZ1':
            self._bytepointer += 1
            if self._bytepointer >= len(byte_array):
                text = 'Repositioning byte pointer failed, corrupted aScreenCap data received'
                logger.warning(text)
                raise AscreencapError(text)
        return byte_array[self._bytepointer:]

    def _screenshot_ascreencap(self):
        raw_compressed_data = self._reposition_byte_pointer(
            self.adb_exec_out([self.config.ASCREENCAP_FILEPATH_REMOTE, '--pack', '2', '--stdout'], serial=self.serial))

        compressed_data_header = np.frombuffer(raw_compressed_data[0:20], dtype=np.uint32)
        if compressed_data_header[0] != 828001602:
            compressed_data_header = compressed_data_header.byteswap()
            if compressed_data_header[0] != 828001602:
                text = f'aScreenCap header verification failure, corrupted image received. ' \
                    f'HEADER IN HEX = {compressed_data_header.tobytes().hex()}'
                logger.warning(text)
                raise AscreencapError(text)

        uncompressed_data_size = compressed_data_header[1].item()
        data = lz4.block.decompress(raw_compressed_data[20:], uncompressed_size=uncompressed_data_size)
        image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        return image

    @retry(wait_fixed=5000, stop_max_attempt_number=10)
    # @timer
    def screenshot(self):
        """
        Returns:
            PIL.Image.Image:
        """
        self._screenshot_interval_timer.wait()
        self._screenshot_interval_timer.reset()
        method = self.config.DEVICE_SCREENSHOT_METHOD

        if method == 'aScreenCap':
            try:
                self.image = self._screenshot_ascreencap()
            except AscreencapError:
                logger.warning('Error when calling aScreenCap, re-initializing')
                self._ascreencap_init()
                self._bytepointer = 0
                self.image = self._screenshot_ascreencap()

        elif method == 'uiautomator2':
            self.image = self._screenshot_uiautomator2()
        else:
            self.image = self._screenshot_adb()

        self.image.load()
        if self.config.ENABLE_ERROR_LOG_AND_SCREENSHOT_SAVE:
            logger.screenshot_deque.append({'time': datetime.now(), 'image': self.image})

        return self.image

    def save_screenshot(self, genre='items', interval=None):
        """Save a screenshot. Use millisecond timestamp as file name.

        Args:
            genre (str, optional): Screenshot type.
            interval (int, float): Seconds between two save. Saves in the interval will be dropped.

        Returns:
            bool: True if save succeed.
        """
        now = time.time()
        if interval is None:
            interval = self.config.SCREEN_SHOT_SAVE_INTERVAL

        if now - self._last_save_time.get(genre, 0) > interval:
            fmt = 'png'
            file = '%s.%s' % (int(now * 1000), fmt)

            folder = os.path.join(self.config.SCREEN_SHOT_SAVE_FOLDER, genre)
            if not os.path.exists(folder):
                os.mkdir(folder)

            file = os.path.join(folder, file)
            self.image.save(file)
            self._last_save_time[genre] = now
            return True
        else:
            self._last_save_time[genre] = now
            return False

    def screenshot_last_save_time_reset(self, genre):
        self._last_save_time[genre] = 0

    def screenshot_interval_set(self, interval):
        if interval < 0.1:
            interval = 0.1
        if interval != self._screenshot_interval_timer.limit:
            logger.info(f'Screenshot interval set to {interval}s')
            self._screenshot_interval_timer.limit = interval
