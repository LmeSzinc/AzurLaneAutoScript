from tasks.base.ui import UI
from tasks.rogue.assets.assets_rogue_ui import *
from tasks.rogue.keywords import *


class RogueUI(UI):
    path: RoguePath
    ocr_blessings: list
    ocr_curios: list
    claimed_blessings: list
    claimed_curios: list

    def is_page_choose_blessing(self):
        return self.image_color_count(PAGE_CHOOSE_BUFF, (245, 245, 245), count=200)

    def is_page_choose_curio(self):
        return self.appear(PAGE_CHOOSE_CURIO)
