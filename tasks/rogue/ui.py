import re

import numpy as np

from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import Digit, Ocr, OcrResultButton
from tasks.base.ui import UI
from tasks.rogue.assets.assets_rogue_blessing import OCR_ROGUE_BUFF
from tasks.rogue.assets.assets_rogue_ui import *
from tasks.rogue.keywords import *
from tasks.rogue.utils import is_card_selected


class RogueBonusOcr(Ocr):
    def after_process(self, result):
        result = super().after_process(result)
        if self.lang == 'ch':
            replace_pattern_dict = {
                "[宇宝][宙审]": "宇宙",
            }
            for pat, replace in replace_pattern_dict.items():
                result = re.sub(pat, replace, result)
        return result


class RogueUI(UI):
    path: RoguePath
    cosmic_fragment_cache: int

    @property
    def cosmic_fragment(self):
        if self.appear(COSMIC_FRAGMENT):
            self.cosmic_fragment_cache = Digit(OCR_COSMIC_FRAGMENT).ocr_single_line(self.device.image)
        return self.cosmic_fragment_cache

    def is_page_choose_blessing(self):
        return (self.image_color_count(PAGE_CHOOSE_BUFF, (245, 245, 245), count=200)
                and self.appear(CHECK_BLESSING))

    def is_page_choose_curio(self):
        return self.appear(PAGE_CHOOSE_CURIO)

    def is_page_choose_bonus(self):
        return self.appear(PAGE_CHOOSE_BONUS)

    def _wait_bonus_page_loaded(self, timer=Timer(0.3, count=1), timeout=Timer(5, count=10)):
        timer.reset()
        timeout.reset()
        while 1:
            self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait bonus page loaded timeout')
                break

            if self.appear(BONUS_BOTTOM_WHITE_BAR):
                if timer.reached():
                    logger.info('Bonus page stabled')
                    break
            else:
                timer.reset()

    def bonus_recognition(self):
        self._wait_bonus_page_loaded()
        ocr = RogueBonusOcr(OCR_ROGUE_BUFF)
        results = ocr.matched_ocr(self.device.image, [RogueBonus])
        expected_count = 3
        if expected_count != len(results):
            logger.warning(f"The OCR result does not match the bonus count. "
                           f"Expect {expected_count}, but recognized {len(results)} only.")
        return results

    def ui_choose_bonus(self, target: OcrResultButton | None, skip_first_screenshot=True):
        interval = Timer(1)
        # start -> select
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if is_card_selected(self, target, confirm_button=BONUS_CONFIRM):
                break
            if interval.reached():
                self.device.click(target)
                interval.reset()

        skip_first_screenshot = True
        # select -> confirm
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.is_in_main() or self.is_page_choose_curio() or self.is_page_choose_blessing():
                break
            if interval.reached():
                self.device.click(BONUS_CONFIRM)
                interval.reset()

    def recognize_and_select_bonus(self):
        results = self.bonus_recognition()
        if not results:
            self.ui_choose_bonus(None)
        options = {result.matched_keyword.en: result for result in results}
        if self.config.Rogue_Bonus not in options.keys():
            logger.warning(f"Can not find option: {self.config.Rogue_Bonus}, randomly choose one")
            target = np.random.choice(options)
        else:
            target = options[self.config.Rogue_Bonus]
        logger.info(f"Choose bonus: {target}")
        self.ui_choose_bonus(target)
