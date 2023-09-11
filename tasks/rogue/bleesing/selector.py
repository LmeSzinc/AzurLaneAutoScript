import numpy as np

from module.logger import logger
from module.ocr.keyword import Keyword
from module.ocr.ocr import OcrResultButton
from tasks.rogue.bleesing.ui import RogueUI


class RogueSelector:
    """
    An Interface used in blessing, curio, and other ui selection in rogue
    """

    def __init__(self, main: RogueUI):
        self.main = main
        self.filter_ = None
        self.ocr_results = []

    def recognition(self):
        ...

    def ui_select(self, target: OcrResultButton | None, skip_first_screenshot=True):
        ...

    def try_select(self, option: OcrResultButton | str):
        ...

    def load_filter(self):
        ...

    def perform_selection(self, priority):
        if not self.ocr_results:
            logger.warning('No blessing recognized, randomly choose one')
            self.ui_select(None)
            return False

        if not len(priority):
            logger.info('No blessing project satisfies current filter, randomly choose one')
            choose = np.random.choice(self.ocr_results)
            self.ui_select(choose)
            return False

        for option in priority:
            logger.info(f"Try to choose option: {option}")
            if self.try_select(option):
                return True
            else:
                logger.info(f"Can not choose option: {option}")

    def apply_filter(self) -> list[Keyword | str]:
        def match_ocr_result(matched_keyword: Keyword):
            for result in self.ocr_results:
                if result.matched_keyword == matched_keyword:
                    return result
            return None

        if self.filter_:
            keywords = [result.matched_keyword for result in self.ocr_results]
            priority = self.filter_.apply(keywords)
            priority = [option if isinstance(option, str) else match_ocr_result(option) for option in priority]
        else:
            logger.warning("No filter loaded, use random instead")
            priority = ['random']
        priority = self.after_process(priority)
        return priority

    def after_process(self, priority) -> list[Keyword | str]:
        """
        Usage: add extra logics to modify the priority
        """
        return priority

    def recognize_and_select(self):
        self.recognition()
        self.load_filter()
        priority = self.apply_filter()
        logger.info(f"Priority: {priority}")
        self.perform_selection(priority)
