from module.ocr.ocr import Digit, DigitCounter
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_prepare import (
    OCR_TRAILBLAZE_POWER,
    OCR_WAVE_COUNT,
    WAVE_MINUS,
    WAVE_PLUS
)


class CombatPrepare(UI):
    def combat_set_wave(self, count=6):
        """
        Args:
            count: 1 to 6

        Pages:
            in: COMBAT_PREPARE
        """
        self.ui_ensure_index(
            count, letter=Digit(OCR_WAVE_COUNT),
            next_button=WAVE_PLUS, prev_button=WAVE_MINUS,
            skip_first_screenshot=True
        )

    def combat_get_trailblaze_power(self) -> int:
        """
        Pages:
            in: COMBAT_PREPARE or COMBAT_REPEAT
        """
        current, _, _ = DigitCounter(OCR_TRAILBLAZE_POWER).ocr_single_line(self.device.image)
        self.state.TrailblazePower = current
        return current
