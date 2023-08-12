from module.ocr.ocr import Digit
from tasks.base.ui import UI
from tasks.rogue.assets.assets_rogue_ui import *
from tasks.rogue.keywords import *


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
