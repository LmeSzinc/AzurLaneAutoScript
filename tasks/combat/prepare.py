import re

from module.logger import logger
from module.ocr.ocr import Ocr
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_prepare import OCR_WAVE_COUNT, WAVE_MINUS, WAVE_PLUS


class WaveCount(Ocr):
    def after_process(self, result):
        """
        Returns:
            int:
        """
        result = super().after_process(result)
        logger.attr(name=self.name, text=str(result))

        res = re.search(r'(\d)', result)
        if res:
            result = int(res.group(1))
            if 1 <= result <= 6:
                return result
            else:
                logger.warning(f'Unexpected combat wave: {result}')
                return 0
        else:
            logger.warning('Cannot find wave count')
            return 0


class CombatPrepare(UI):
    def combat_set_wave(self, count=6):
        """
        Args:
            count: 1 to 6
        """
        self.ui_ensure_index(
            count, letter=WaveCount(OCR_WAVE_COUNT),
            next_button=WAVE_PLUS, prev_button=WAVE_MINUS,
            skip_first_screenshot=True
        )
