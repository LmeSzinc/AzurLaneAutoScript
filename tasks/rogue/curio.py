import re

import numpy as np

from module.base.filter import MultiLangFilter
from module.base.timer import Timer
from module.base.utils import get_color
from module.logger import logger
from module.ocr.ocr import Ocr, OcrResultButton
from tasks.rogue.assets.assets_rogue_curio import *
from tasks.rogue.assets.assets_rogue_ui import BLESSING_CONFIRM
from tasks.rogue.keywords import RogueCurio
from tasks.rogue.preset import CURIO_PRESET_1
from tasks.rogue.selector import RogueSelector
from tasks.rogue.utils import get_regex_from_keyword_name, parse_name

CURIO_FILTER_ATTR = tuple()
CURIO_ATTR_NAME = 'curio_name'
pattern = get_regex_from_keyword_name(RogueCurio, CURIO_ATTR_NAME)
CURIO_FILTER_ATTR += (CURIO_ATTR_NAME,)
CURIO_FILTER_PRESET = ('random',)
FILTER_REGEX = re.compile(pattern)
CURIO_FILTER = MultiLangFilter(FILTER_REGEX, CURIO_FILTER_ATTR, CURIO_FILTER_PRESET)


class RogueCurioOcr(Ocr):
    merge_thres_y = 40

    def after_process(self, result):
        result = super().after_process(result)
        if self.lang == 'ch':
            replace_pattern_dict = {
                "般": "骰",
                "漂灭": "湮灭",
            }
            for pattern, replace in replace_pattern_dict.items():
                result = re.sub(pattern, replace, result)
        return result


class RogueCurioSelector(RogueSelector):
    def recognition(self):
        self.ocr_results = []
        ocr = RogueCurioOcr(OCR_ROGUE_CURIO)
        results = ocr.matched_ocr(self.main.device.image, RogueCurio)
        expect_num = 3
        if len(results) != expect_num:
            logger.warning(f"The OCR result does not match the curio count. "
                           f"Expect {expect_num}, but recognized {len(results)} only.")
        self.ocr_results = results
        return results

    def ui_select(self, target: OcrResultButton | None, skip_first_screenshot=True):
        def is_curio_selected():
            return np.mean(get_color(self.main.device.image, tuple(target.area))) > 70  # shiny background

        def is_select_curio_complete():
            """
                Case 1: back to main page
                Case 2: event page
            """
            return self.main.is_in_main() or self.main.is_page_event()

        enforce = False
        if not target:
            enforce = True
        interval = Timer(1)
        # start -> selected
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.main.device.screenshot()

            if is_curio_selected():
                if enforce:
                    logger.info("Curio selected (enforce)")
                else:
                    logger.info(f"Curio {target} selected")
                break
            if interval.reached():
                if enforce:
                    self.main.device.click(CURIO_ENFORCE)
                else:
                    self.main.device.click(target)
                interval.reset()

        skip_first_screenshot = True
        # selected -> confirm
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.main.device.screenshot()

            if is_select_curio_complete():
                break
            if interval.reached():
                self.main.device.click(BLESSING_CONFIRM)
                interval.reset()

    def try_select(self, option: OcrResultButton | str):
        if option == 'random':
            target = np.random.choice(self.ocr_results)
            self.ui_select(target)
            return True
        if isinstance(option, OcrResultButton):
            self.ui_select(option)
            return True
        return False

    def load_filter(self):
        filter_ = CURIO_FILTER
        if self.main.config.Rogue_PresetCurioFilter == 'preset-1':
            filter_.load(parse_name(CURIO_PRESET_1))
        if self.main.config.Rogue_PresetCurioFilter == 'custom':
            filter_.load(parse_name(self.main.config.Rogue_CustomCurioFilter))
        self.filter_ = filter_
