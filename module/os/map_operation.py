from module.base.utils import *
from module.base.decorator import Config
from module.map.map_operation import MapOperation
from module.os.assets import *
from module.ocr.ocr import Ocr
from module.logger import logger
from module.os.map_data import DIC_OS_MAP


class OSMapOperation(MapOperation):
    os_map_name = 'Unknown'

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

    @Config.when(SERVER='en')
    def get_map_shape(self):
        # For EN only
        from string import whitespace
        ocr = Ocr(MAP_NAME, lang='cnocr', letter=(214, 235, 235), threshold=96, name='OCR_OS_MAP_NAME')
        name = ocr.ocr(self.device.image)
        name = name.translate(dict.fromkeys(map(ord, whitespace)))
        if '-' in name:
            name = name.split('-')[0]

        logger.info(f'Map name processed: {name}')
        name = name.lower()
        if 'nvcity' in name: # NY City Port read as 'V' rather than 'Y'
            name = 'nycity'

        for index, chapter in DIC_OS_MAP.items():
            cmp_name = chapter['en'].translate(dict.fromkeys(map(ord, whitespace)))
            cmp_name = cmp_name.lower()
            if 'é' in cmp_name: # Méditerranée name maps
                cmp_name = cmp_name.replace('é', 'e')

            if name == cmp_name:
                self.os_map_name = chapter['en']
                logger.info(
                    f"Current OS map: {chapter['en']}, "
                    f"id: {index}, shape: {chapter['shape']}, hazard_level: {chapter['hazard_level']}"
                )
                return chapter['shape']

        logger.warning('Unknown OS map')
        exit(1)

    @Config.when(SERVER=None)
    def get_map_shape(self):
        # For CN only
        ocr = Ocr(MAP_NAME, lang='cnocr', letter=(235, 235, 235), threshold=160, name='OCR_OS_MAP_NAME')
        name = ocr.ocr(self.device.image)
        if '-' in name:
            name = name.split('-')[0]
        else:
            name = name.rstrip('安全海域-')
        logger.info(f'Map name processed: {name}')

        for index, chapter in DIC_OS_MAP.items():
            if name == chapter['cn']:
                self.os_map_name = name
                logger.info(
                    f"Current OS map: {chapter['cn']}, "
                    f"id: {index}, shape: {chapter['shape']}, hazard_level: {chapter['hazard_level']}"
                )
                return chapter['shape']

        logger.warning('Unknown OS map')
        exit(1)
