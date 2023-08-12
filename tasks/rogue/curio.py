import re

import numpy as np

from module.base.timer import Timer
from module.base.utils import get_color
from module.logger import logger
from module.ocr.ocr import Ocr, OcrResultButton
from tasks.rogue.assets.assets_rogue_curio import *
from tasks.rogue.assets.assets_rogue_ui import CONFIRM
from tasks.rogue.keywords import RogueCurio
from tasks.rogue.ui import RogueUI


class RogueCurioOcr(Ocr):
    def after_process(self, result):
        result = super().after_process(result)
        if self.lang == 'ch':
            replace_pattern_dict = {
                "降维般子": "降维骰子"
            }
            for pattern, replace in replace_pattern_dict.items():
                result = re.sub(pattern, replace, result)
        return result


class RogueCurioUI(RogueUI):
    def curio_recognition(self):
        ocr = RogueCurioOcr(OCR_ROGUE_CURIO)
        results = ocr.matched_ocr(self.device.image, RogueCurio)
        expect_num = 3
        if len(results) != expect_num:
            logger.warning(f"The OCR result does not match the curio count. "
                           f"Expect {expect_num}, but recognized {len(results)} only.")
        self.ocr_curios = results
        return results

    def ui_select_curio(self, curio: OcrResultButton | None, skip_first_screenshot=True, enforce=True):
        def is_curio_selected():
            return np.mean(get_color(self.device.image, tuple(curio.area))) > 70

        def is_select_curio_complete():
            """
                Case 1: back to main page
            """
            return self.is_in_main()

        interval = Timer(1)
        # start -> selected
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if is_curio_selected():
                if enforce:
                    logger.info("Curio selected (enforce)")
                else:
                    logger.info(f"Curio {curio} selected")
                break
            if interval.reached():
                if enforce:
                    self.device.click(CURIO_ENFORCE)
                else:
                    self.device.click(curio)
                interval.reset()

        skip_first_screenshot = True
        # selected -> confirm
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if is_select_curio_complete():
                break
            if interval.reached():
                self.device.click(CONFIRM)
                interval.reset()
