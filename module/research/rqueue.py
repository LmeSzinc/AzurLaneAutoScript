from module.base.timer import Timer
from module.handler.assets import POPUP_CANCEL, POPUP_CONFIRM
from module.logger import logger
from module.research.assets import *
from module.ui.assets import RESEARCH_CHECK
from module.ui.ui import UI


class ResearchQueue(UI):
    def is_in_research(self):
        return self.appear(RESEARCH_CHECK, offset=(20, 20))

    def research_queue_add(self, skip_first_screenshot=True):
        """
        Pages:
            in: RESEARCH_QUEUE_ADD (is_in_research, DETAIL_NEXT)
            out: is_in_research and stabled
        """
        logger.info('Research queue add')
        confirm_timer = Timer(0.3, count=1)
        # POPUP_CONFIRM has just been clicked in research_project_start()
        self.interval_clear([POPUP_CANCEL, POPUP_CONFIRM])
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.is_in_research() and not self.appear(DETAIL_NEXT, offset=(20, 20)):
                # Not in detail page
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

            if self.appear_then_click(RESEARCH_QUEUE_ADD, offset=(20, 20), interval=3):
                continue
            if self.handle_popup_confirm('RESEARCH_QUEUE'):
                continue

        self.wait_until_stable(STABLE_CHECKER_CENTER)
