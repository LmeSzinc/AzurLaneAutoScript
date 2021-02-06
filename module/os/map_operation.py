from module.base.utils import *
from module.base.decorator import Config
import module.config.server as server
from module.map.map_operation import MapOperation
from module.os.assets import *
from module.ocr.ocr import Ocr
from module.logger import logger
from module.os.map_data import DIC_OS_MAP


class OSMapOperation(MapOperation):
    os_map_name = 'Unknown'

    @Config.when(SERVER='en')
    def _ocr_map_name(self):
        return Ocr(MAP_NAME, lang='cnocr', letter=(214, 235, 235), threshold=160, name='OCR_OS_MAP_NAME')

    @Config.when(SERVER='cn')
    def _ocr_map_name(self):
        return Ocr(MAP_NAME, lang='cnocr', letter=(235, 235, 235), threshold=160, name='OCR_OS_MAP_NAME')

    def is_meowfficer_searching(self):
        """
        Returns:
            bool:

        Page:
            in: IN_MAP
        """
        return self.appear(MEOWFFICER_SEARCHING, offset=(10, 10))

    def get_meowfficer_searching_percentage(self):
        """
        Returns:
            float: 0 to 1.

        Pages:
            in: IN_MAP, is_meowfficer_searching == True
        """
        return color_bar_percentage(
            self.device.image, area=MEOWFFICER_SEARCHING_PERCENTAGE.area, prev_color=(74, 223, 255))

    def get_map_shape(self):
        name = self._ocr_map_name().ocr(self.device.image)
        if '-' in name:
            name = name.split('-')[0]
        else:
            name = name.rstrip('安全海域-')
        logger.info(f'Map name processed: {name}')

        for index, chapter in DIC_OS_MAP.items():
            if name == chapter[server.server]:
                self.os_map_name = name
                logger.info(
                    f"Current OS map: {chapter[server.server]}, "
                    f"id: {index}, shape: {chapter['shape']}, hazard_level: {chapter['hazard_level']}"
                )
                return chapter['shape']

        logger.warning('Unknown OS map')
        exit(1)
