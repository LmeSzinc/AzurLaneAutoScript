import re

from module.base.utils import area_offset
from module.logger import logger
from module.ocr.ocr import Digit, Ocr, OcrResultButton
from tasks.base.ui import UI
from tasks.rogue.assets.assets_rogue_reward import REWARD_ENTER
from tasks.rogue.assets.assets_rogue_ui import *
from tasks.rogue.keywords import RoguePath


class RogueBonusOcr(Ocr):
    def after_process(self, result):
        result = super().after_process(result)
        if self.lang == 'cn':
            replace_pattern_dict = {
                "[宇宝][宙审]": "宇宙",
            }
            for pat, replace in replace_pattern_dict.items():
                result = re.sub(pat, replace, result)
        return result


class RogueUI(UI):
    path: RoguePath

    @property
    def cosmic_fragment(self):
        """
        Return valid result only when template appear
        """
        if self.appear(COSMIC_FRAGMENT):
            return Digit(OCR_COSMIC_FRAGMENT).ocr_single_line(self.device.image)
        return 0

    def is_page_choose_blessing(self):
        return (self.image_color_count(PAGE_CHOOSE_BUFF, (245, 245, 245), count=200)
                and self.appear(CHECK_BLESSING))

    def is_page_choose_curio(self):
        return self.appear(PAGE_CHOOSE_CURIO)

    def is_page_choose_bonus(self):
        return self.appear(PAGE_CHOOSE_BONUS)

    def is_page_event(self):
        return self.appear(PAGE_EVENT)

    def is_page_rogue_main(self):
        return self.match_template_color(REWARD_ENTER)

    def is_page_rogue_launch(self):
        return self.match_template_color(ROGUE_LAUNCH)

    def handle_obtain_item_popup(self, interval=5) -> bool:
        """After selecting some curio (e.g. Sealing_Wax_of_*), there will be a popup after back to main page"""
        if self.appear_then_click(OBTAIN_ITEM_POPUP, interval=interval):
            return True
        return False

    def is_unrecorded(self, target: OcrResultButton, relative_area):
        """
        To check a rogue keyword is not record in game index by finding template
        """
        FLAG_UNRECORD.matched_button.search = area_offset(relative_area, target.area[:2])
        return self.appear(FLAG_UNRECORD)

    def handle_blessing_popup(self):
        # Obtained a free blessing from curio
        if self.appear(BLESSING_OBTAINED, interval=2):
            logger.info(f'{BLESSING_OBTAINED} -> {BLESSING_CONFIRM}')
            self.device.click(BLESSING_CONFIRM)
            return True
        # Enhanced a blessing from occurrence
        if self.appear(BLESSING_ENHANCED, interval=2):
            logger.info(f'{BLESSING_ENHANCED} -> {BLESSING_CONFIRM}')
            self.device.click(BLESSING_CONFIRM)
            return True
        # Lost and re-obtain blessing, randomized by curio
        if self.appear(BLESSING_LOST, interval=2):
            logger.info(f'{BLESSING_LOST} -> {BLESSING_CONFIRM}')
            self.device.click(BLESSING_CONFIRM)
            return True
        return False
