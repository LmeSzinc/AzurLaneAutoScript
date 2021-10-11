import os

import cv2
import lz4.block
import numpy as np
from PIL import Image

from module.device.connection import Connection
from module.exception import RequestHumanTakeover
from module.logger import logger


class AscreencapError(Exception):
    pass


class AScreenCap(Connection):
    _bytepointer = 0

    def _ascreencap_init(self):
        logger.hr('aScreenCap init')

        arc = self.adb_exec_out(['getprop', 'ro.product.cpu.abi']).decode('utf-8').strip()
        sdk = self.adb_exec_out(['getprop', 'ro.build.version.sdk']).decode('utf-8').strip()
        logger.info(f'cpu_arc: {arc}, sdk_ver: {sdk}')

        filepath = os.path.join(self.config.ASCREENCAP_FILEPATH_LOCAL, arc, 'ascreencap')
        if int(sdk) not in range(21, 26) or not os.path.exists(filepath):
            logger.critical('No suitable version of aScreenCap lib available for this device')
            logger.critical('Please use ADB or uiautomator2 for screenshots instead')
            raise RequestHumanTakeover

        logger.info(f'pushing {filepath}')
        self.adb_push([filepath, self.config.ASCREENCAP_FILEPATH_REMOTE])

        logger.info(f'chmod 0777 {self.config.ASCREENCAP_FILEPATH_REMOTE}')
        self.adb_shell(['chmod', '0777', self.config.ASCREENCAP_FILEPATH_REMOTE])

    def _ascreencap_reposition_byte_pointer(self, byte_array):
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

    def _ascreencap_execute(self):
        raw_compressed_data = self._ascreencap_reposition_byte_pointer(
            self.adb_exec_out([self.config.ASCREENCAP_FILEPATH_REMOTE, '--pack', '2', '--stdout']))

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

    def _screenshot_ascreencap(self):
        try:
            return self._ascreencap_execute()
        except AscreencapError:
            logger.warning('Error when calling aScreenCap, re-initializing')
            self._ascreencap_init()
            self._bytepointer = 0
            return self._ascreencap_execute()
