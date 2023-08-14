import re

from module.ocr.ocr import Digit, Ocr
from tasks.base.ui import UI
from tasks.rogue.assets.assets_rogue_ui import *
from tasks.rogue.keywords import *


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
