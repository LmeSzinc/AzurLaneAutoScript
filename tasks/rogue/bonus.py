import numpy as np

from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import OcrResultButton
from tasks.rogue.assets.assets_rogue_blessing import OCR_ROGUE_BUFF
from tasks.rogue.assets.assets_rogue_bonus import BONUS_BOTTOM_WHITE_BAR, BONUS_CONFIRM
from tasks.rogue.keywords import RogueBonus
from tasks.rogue.selector import RogueSelector
from tasks.rogue.ui import RogueBonusOcr
from tasks.rogue.utils import is_card_selected


class RogueBonusSelector(RogueSelector):
    def _wait_bonus_page_loaded(self, timer=Timer(0.3, count=1), timeout=Timer(5, count=10)):
        timer.reset()
        timeout.reset()
        while 1:
            self.main.device.screenshot()

            if timeout.reached():
                logger.warning('Wait bonus page loaded timeout')
                break

            if self.main.appear(BONUS_BOTTOM_WHITE_BAR):
                if timer.reached():
                    logger.info('Bonus page stabled')
                    break
            else:
                timer.reset()

    def recognition(self):
        self._wait_bonus_page_loaded()
        ocr = RogueBonusOcr(OCR_ROGUE_BUFF)
        results = ocr.matched_ocr(self.main.device.image, [RogueBonus])
        expected_count = 3
        if expected_count != len(results):
            logger.warning(f"The OCR result does not match the bonus count. "
                           f"Expect {expected_count}, but recognized {len(results)} only.")
        self.ocr_results = results
        return results

    def ui_select(self, target: OcrResultButton | None, skip_first_screenshot=True):
        interval = Timer(1)
        # start -> select
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.main.device.screenshot()

            if is_card_selected(self.main, target, confirm_button=BONUS_CONFIRM):
                break
            if interval.reached():
                self.main.device.click(target)
                interval.reset()

        skip_first_screenshot = True
        # select -> confirm
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.main.device.screenshot()

            if self.main.is_in_main():
                logger.info("Main Page Checked")
                break
            if self.main.is_page_choose_curio():
                logger.info("Choose curio page checked")
                break
            if self.main.is_page_choose_blessing():
                logger.info("Choose blessing page checked")
                break
            if interval.reached():
                self.main.device.click(BONUS_CONFIRM)
                interval.reset()

    def recognize_and_select(self):
        self.recognition()
        if not self.ocr_results:
            self.ui_select(None)
        options = {result.matched_keyword.en: result for result in self.ocr_results}
        if self.main.config.RoguePath_Bonus not in options.keys():
            logger.warning(f"Can not find option: {self.main.config.RoguePath_Bonus}, randomly choose one")
            target = np.random.choice(options)
        else:
            target = options[self.main.config.RoguePath_Bonus]
        logger.info(f"Choose bonus: {target}")
        self.ui_select(target)
