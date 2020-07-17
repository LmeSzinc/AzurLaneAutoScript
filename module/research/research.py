import numpy as np

from module.base.timer import Timer
from module.base.utils import get_color
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2, GET_ITEMS_3
from module.logger import logger
from module.research.assets import *
from module.research.project import ResearchSelector
from module.ui.ui import page_research, page_main, RESEARCH_CHECK

RESEARCH_ENTRANCE = [ENTRANCE_1, ENTRANCE_2, ENTRANCE_3, ENTRANCE_4, ENTRANCE_5]


class RewardResearch(ResearchSelector):
    def ensure_research_stable(self):
        self.wait_until_stable(STABLE_CHECKER)

    def _in_research(self):
        return self.appear(RESEARCH_CHECK, offset=(20, 20))

    def research_has_finished(self):
        """
        Returns:
            bool: True if a research finished
        """
        color = get_color(self.device.image, CURRENT_PROJECT_STATUS.area)
        if np.max(color) - np.min(color) < 40:
            logger.warning(f'Unexpected color: {color}')
        index = np.argmax(color)  # R, G, B
        if index == 1:
            return True  # Green
        elif index == 2:
            return False  # Blue
        else:
            logger.warning(f'Unexpected color: {color}')
            return False

    def research_reset(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot (bool):

        Returns:
            bool: If reset success.
        """
        if not self.appear(RESET_AVAILABLE):
            logger.info('Research reset unavailable')
            return False

        logger.info('Research reset')
        executed = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(RESET_AVAILABLE, interval=10):
                continue
            if self.handle_popup_confirm('RESEARCH_RESET'):
                executed = True
                continue

            # End
            if executed and self._in_research():
                self.ensure_no_info_bar()  # Refresh success
                self.ensure_research_stable()
                break

        return True

    def research_select(self):
        """
        Get best research and able to use research reset.

        Returns:
            int: Research project index from left to right. None if no project satisfied.
        """
        for _ in range(2):
            self.research_detect(self.device.image)
            priority = self.research_sort_filter()

            # priority example: ['reset', 'shortest']
            if not len(priority):
                return None
            if priority[0] == 'reset':
                if self.research_reset():
                    continue
                else:
                    priority.pop(0)

            # priority example: ['shortest']
            if not len(priority):
                return None
            if isinstance(priority[0], str):
                method = priority[0]
                if method == 'shortest':
                    priority = self.research_sort_shortest()
                elif method == 'cheapest':
                    priority = self.research_sort_cheapest()
                else:
                    logger.warning(f'Unknown select method: {method}')

            # priority example: [2, 1, 4, 0, 3]
            if not len(priority):
                return None
            else:
                return priority[0]

    def research_project_start(self, index, skip_first_screenshot=True):
        logger.info(f'Research project: {index}')
        click_timer = Timer(10)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Don't use interval here, RESEARCH_CHECK already appeared 5 seconds ago
            if click_timer.reached() and self.appear(RESEARCH_CHECK, offset=(20, 20)):
                self.device.click(RESEARCH_ENTRANCE[index])
                click_timer.reset()
                continue
            if self.appear_then_click(RESEARCH_START, interval=10):
                continue
            if self.handle_popup_confirm('RESEARCH_START'):
                continue

            # End
            if self.appear(RESEARCH_STOP):
                self.ensure_no_info_bar()  # Research started
                break

    def research_receive(self, skip_first_screenshot=True, save_get_items=False):
        logger.info('Research receive')
        executed = False
        # Hacks to change save folder
        backup = self.config.SCREEN_SHOT_SAVE_FOLDER
        self.config.SCREEN_SHOT_SAVE_FOLDER = self.config.SCREEN_SHOT_SAVE_FOLDER_BASE

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(RESEARCH_CHECK, interval=10):
                if save_get_items:
                    self.device.save_screenshot('research_project')
                self.device.click(RESEARCH_ENTRANCE[2])
                continue

            if self.appear(GET_ITEMS_1, interval=5):
                if save_get_items:
                    self.device.sleep(2)
                    self.device.screenshot()
                    self.device.save_screenshot('research_items')
                self.device.click(GET_ITEMS_RESEARCH_SAVE)
                executed = True
                continue
            if self.appear(GET_ITEMS_2, interval=5):
                if save_get_items:
                    self.device.sleep(3)
                    self.device.screenshot()
                    self.device.save_screenshot('research_items')
                self.device.click(GET_ITEMS_RESEARCH_SAVE)
                executed = True
                continue
            if self.appear(GET_ITEMS_3, interval=5):
                if save_get_items:
                    self.device.sleep(4)
                    self.device.screenshot()
                    self.device.save_screenshot('research_items')
                    self.device.swipe((0, 250), box=ITEMS_3_SWIPE.area, random_range=(-10, -10, 10, 10), padding=0)
                    self.device.sleep(2)
                    self.device.screenshot()
                    self.device.save_screenshot('research_items', interval=0)
                self.device.click(GET_ITEMS_RESEARCH_SAVE)
                executed = True
                continue

            # End
            if executed and self._in_research():
                self.ensure_research_stable()
                break

        self.config.SCREEN_SHOT_SAVE_FOLDER_FOLDER = backup

    def research_reward(self):
        """
        Receive research reward and start new research.
        Unable to detect research is running.

        Pages:
            in: page_research, stable.
            out: page_research, has research project information, but it's still page_research.
        """
        logger.hr('Research start')
        if self.research_has_finished():
            self.research_receive(save_get_items=self.config.ENABLE_SAVE_GET_ITEMS)

        index = self.research_select()
        self.research_project_start(index)

    def handle_research_reward(self):
        """
        Pages:
            in: page_reward
            out: page_main
        """
        if not self.config.ENABLE_RESEARCH_REWARD:
            return False

        if not self.appear(RESEARCH_FINISHED) and not self.appear(RESEARCH_PENDING):
            logger.info('No research finished or pending')
            self.ui_goto(page_main, skip_first_screenshot=True)
            return False

        self.ui_goto(page_research, skip_first_screenshot=True)
        self.ensure_research_stable()

        self.research_reward()

        self.ui_goto(page_main, skip_first_screenshot=True)
        return True
