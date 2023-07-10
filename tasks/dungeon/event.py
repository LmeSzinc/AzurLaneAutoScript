from module.logger import logger
from module.ocr.ocr import DigitCounter
from tasks.base.ui import UI
from tasks.dungeon.assets.assets_dungeon_event import DOUBLE_CALYX_EVENT_TAG, OCR_DOUBLE_EVENT_REMAIN


class DungeonEvent(UI):
    def has_double_calyx_event(self) -> bool:
        """
        Pages:
            in: page_guide, Survival_Index, nav at top
        """
        has = self.image_color_count(DOUBLE_CALYX_EVENT_TAG, color=(252, 209, 123), threshold=221, count=50)
        logger.attr('Double calyx', has)
        return has

    def get_double_event_remain(self) -> int:
        """
        Pages:
            in: page_guide, Survival_Index, selected at the nav with double event
        """
        ocr = DigitCounter(OCR_DOUBLE_EVENT_REMAIN)
        remain, _, total = ocr.ocr_single_line(self.device.image)
        if total != 12:
            logger.warning(f'Invalid double event remain')
            remain = 0
        logger.attr('Double event remain', remain)
        return remain
