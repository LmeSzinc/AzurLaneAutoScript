import re

from module.base.timer import Timer
from module.ocr.ocr import Digit, DigitCounter
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_prepare import (
    OCR_TRAILBLAZE_POWER,
    OCR_WAVE_COUNT,
    WAVE_MINUS,
    WAVE_PLUS
)


class TrailblazePowerOcr(DigitCounter):
    def after_process(self, result):
        result = super().after_process(result)
        # The trailblaze power icon is recognized as 买
        # OCR_TRAILBLAZE_POWER includes the icon because the length varies by value
        result = re.sub(r'[买米装：（）]', '', result)
        return result


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

    def combat_has_multi_wave(self) -> bool:
        """
        If combat has waves to set.
        Most dungeons can do 6 times at one time while bosses don't.
        """
        return self.appear(WAVE_MINUS) or self.appear(WAVE_PLUS)

    def combat_get_trailblaze_power(self, expect_reduce=False, skip_first_screenshot=True) -> int:
        """
        Args:
            expect_reduce: Current value is supposed to be lower than the previous.
            skip_first_screenshot:

        Pages:
            in: COMBAT_PREPARE or COMBAT_REPEAT
        """
        timeout = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            current, _, _ = TrailblazePowerOcr(OCR_TRAILBLAZE_POWER).ocr_single_line(self.device.image)
            # Confirm if it is > 180, sometimes just OCR errors
            if current > 180 and timeout.reached():
                break
            if expect_reduce and current >= self.state.TrailblazePower:
                continue
            if current <= 180:
                break

        self.state.TrailblazePower = current
        return current
