import numpy as np

from module.base.decorator import Config
from module.base.timer import Timer
from module.base.utils import get_color, rgb2gray
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2, GET_ITEMS_3
from module.logger import logger
from module.research.assets import *
from module.research.project import ResearchSelector
from module.ui.page import *

RESEARCH_ENTRANCE = [ENTRANCE_1, ENTRANCE_2, ENTRANCE_3, ENTRANCE_4, ENTRANCE_5]
RESEARCH_STATUS = [STATUS_1, STATUS_2, STATUS_3, STATUS_4, STATUS_5]


class RewardResearch(ResearchSelector):
    _research_project_offset = 0
    _research_finished_index = 2

    def ensure_research_stable(self):
        self.wait_until_stable(STABLE_CHECKER)

    def wait_until_get_items_stable(self, timeout=Timer(1, count=2).start(), skip_first_screenshot=True):
        """
        Items in research are shown one by one, row by row,
        which will mis-detect GET_ITEMS_2 as GET_ITEMS_1, or mis-detect GET_ITEMS_3 as GET_ITEMS_1.

        Pages:
            in: GET_ITEMS_<any>
            out: GET_ITEMS_<stabled>
        """
        prev = ''
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            name = ''
            for button in [GET_ITEMS_1, GET_ITEMS_2, GET_ITEMS_3]:
                if self.appear(button):
                    name = button.name
                    break

            # End
            if len(name) and name == prev:
                if timeout.reached():
                    break
            else:
                timeout.reset()
            prev = name

    def _in_research(self):
        return self.appear(RESEARCH_CHECK, offset=(20, 20))

    def _research_has_finished_at(self, button):
        """
        Args:
            button (Button):

        Returns:
            bool: True if a research finished
        """
        color = get_color(self.device.image, button.area)
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

    def research_has_finished(self):
        """
        Finished research should be auto-focused to the center, but sometimes didn't, due to an unknown game bug.
        This method will handle that.

        Returns:
            bool: True if a research finished
        """
        for index, button in enumerate(RESEARCH_STATUS):
            if self._research_has_finished_at(button):
                logger.attr('Research_finished', index)
                self._research_finished_index = index
                return True

        return False

    def research_reset(self, skip_first_screenshot=True, save_get_items=False):
        """
        Args:
            skip_first_screenshot (bool):
            save_get_items (bool):

        Returns:
            bool: If reset success.
        """
        if not self.appear(RESET_AVAILABLE):
            logger.info('Research reset unavailable')
            return False

        logger.info('Research reset')
        executed = False
        if save_get_items:
            self.device.save_screenshot('research_project', interval=0, to_base_folder=True)
        self.stat.add(self.device.image)
        self.stat.upload()
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
                self.ensure_no_info_bar(timeout=3)  # Refresh success
                self.ensure_research_stable()
                break

        return True

    def research_select(self, priority, save_get_items=False):
        """
        Args:
            priority (list): A list of str and int, such as [2, 3, 0, 'reset']
            save_get_items (bool):

        Returns:
            bool: False if have been reset
        """
        if not len(priority):
            logger.info('No research project satisfies current filter')
            return True
        for project in priority:
            # priority example: ['reset', 'shortest']
            if project == 'reset':
                if self.research_reset(save_get_items=save_get_items):
                    return False
                else:
                    continue

            if isinstance(project, str):
                # priority example: ['shortest']
                if project == 'shortest':
                    self.research_select(self.research_sort_shortest(), save_get_items=save_get_items)
                elif project == 'cheapest':
                    self.research_select(self.research_sort_cheapest(), save_get_items=save_get_items)
                else:
                    logger.warning(f'Unknown select method: {project}')
                return True
            else:
                # priority example: [2, 3, 0]
                if self.research_project_start(project):
                    return True
                else:
                    continue

        logger.info('No research project started')
        return True

    def research_project_start(self, index, skip_first_screenshot=True):
        """
        Args:
            index (int): 0 to 4.
            skip_first_screenshot:

        Returns:
            bool: If start success.
        """
        logger.info(f'Research project: {index}')
        available = False
        click_timer = Timer(10)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            max_rgb = np.max(rgb2gray(np.array(self.image_area(RESEARCH_UNAVAILABLE))))

            # Don't use interval here, RESEARCH_CHECK already appeared 5 seconds ago
            if click_timer.reached() and self.appear(RESEARCH_CHECK, offset=(20, 20)):
                i = (index - self._research_project_offset) % 5
                logger.info(f'Project offset: {self._research_project_offset}, project {index} is at {i}')
                self.device.click(RESEARCH_ENTRANCE[i])
                self._research_project_offset = (index - 2) % 5
                self.ensure_research_stable()
                click_timer.reset()
                continue
            if max_rgb > 235 and self.appear_then_click(RESEARCH_START, offset=(5, 20), interval=10):
                available = True
                continue
            if self.handle_popup_confirm('RESEARCH_START'):
                continue

            # End
            if self.appear(RESEARCH_STOP, offset=(20, 20)):
                # RESEARCH_STOP is a semi-transparent button, color will vary depending on the background.
                self.research_detail_quit()
                self.ensure_no_info_bar(timeout=3)  # Research started
                return True
            if not available and max_rgb <= 235 and self.appear(RESEARCH_UNAVAILABLE, offset=(5, 20)):
                logger.info('Not enough resources to start this project')
                self.research_detail_quit()
                return False

    def research_receive(self, skip_first_screenshot=True, save_get_items=False):
        logger.info('Research receive')
        timeout = Timer(40).start()
        executed = False

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot_interval_set(0.5)
                self.device.screenshot()

            if self.appear(RESEARCH_CHECK, interval=10):
                if self._research_has_finished_at(RESEARCH_STATUS[self._research_finished_index]):
                    if save_get_items:
                        self.device.save_screenshot('research_project', interval=0, to_base_folder=True)
                    self.stat.add(self.device.image)
                    self.device.click(RESEARCH_ENTRANCE[self._research_finished_index])
                    continue

            if self.appear(GET_ITEMS_1, interval=5):
                self.wait_until_get_items_stable()
                logger.info('Get items 1 stabled')
                if not self.appear(GET_ITEMS_1, interval=0):
                    continue
                self.device.sleep(2)
                if save_get_items:
                    self.device.screenshot()
                    self.device.save_screenshot('research_items', to_base_folder=True)
                self.stat.add(self.device.image)
                self.stat.upload()
                self.device.click(GET_ITEMS_RESEARCH_SAVE)
                executed = True
                continue
            if self.appear(GET_ITEMS_2, interval=5):
                self.wait_until_get_items_stable()
                logger.info('Get items 2 stabled')
                if not self.appear(GET_ITEMS_2, interval=0):
                    continue
                self.device.sleep(2)
                if save_get_items:
                    self.device.screenshot()
                    self.device.save_screenshot('research_items', to_base_folder=True)
                self.stat.add(self.device.image)
                self.stat.upload()
                self.device.click(GET_ITEMS_RESEARCH_SAVE)
                executed = True
                continue
            if self.appear(GET_ITEMS_3, interval=5):
                self.wait_until_get_items_stable()
                logger.info('Get items 3 stabled')
                if not self.appear(GET_ITEMS_3, interval=0):
                    continue
                self.device.sleep(3)
                if save_get_items or self.config.ENABLE_AZURSTAT:
                    self.device.screenshot()
                    if save_get_items:
                        self.device.save_screenshot('research_items', to_base_folder=True)
                    self.stat.add(self.device.image)
                    self.device.swipe((0, 250), box=ITEMS_3_SWIPE.area, random_range=(-10, -10, 10, 10), padding=0)
                    self.device.sleep(2)
                    self.device.screenshot()
                    if save_get_items:
                        self.device.save_screenshot('research_items', interval=0, to_base_folder=True)
                    self.stat.add(self.device.image)
                    self.stat.upload()
                self.device.click(GET_ITEMS_RESEARCH_SAVE)
                executed = True
                continue

            # End
            if executed and self._in_research():
                self.ensure_research_stable()
                break
            if timeout.reached():
                logger.warning(f'research_receive timeout, executed={executed}, _in_research={self._in_research()}')
                break

        self.device.screenshot_interval_set(0.1)
        self.stat.clear()

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
        else:
            logger.info('No research has finished')

        self._research_project_offset = 0

        for _ in range(2):
            self.research_detect(self.device.image)
            priority = self.research_sort_filter()
            result = self.research_select(priority, save_get_items=self.config.ENABLE_SAVE_GET_ITEMS)
            if result:
                break

    @Config.when(SERVER='en')
    def ui_ensure_research(self):
        """
        In EN, the title of page_reshmenu and page_research are "Technology",
        so RESEARCH_CHECK in EN uses "Resets daily in midnight".
        However it's loaded faster then other objects in page_research.
        To handle this, check both "Technology" and "Resets daily in midnight".

        Pages:
            in: Any page
            out: page_research
        """

        def research_check():
            return self.appear(RESEARCH_CHECK, offset=(20, 20)) and self.appear(RESEARCH_TITLE, offset=(20, 20))

        self.ui_goto(page_reshmenu, skip_first_screenshot=True)
        self.ui_click(RESHMENU_GOTO_RESEARCH, check_button=research_check, skip_first_screenshot=True)
        self.device.send_notification('Research Start', 'Research receive')
        self.ensure_research_stable()

    @Config.when(SERVER=None)
    def ui_ensure_research(self):
        """
        Pages:
            in: Any page
            out: page_research
        """
        self.ui_goto(page_research, skip_first_screenshot=True)
        self.ensure_research_stable()

    def handle_research_reward(self):
        """
        Pages:
            in: page_reward
            out: page_research or page_reward
        """
        if not self.config.ENABLE_RESEARCH_REWARD:
            return False

        if not self.appear(RESEARCH_FINISHED) and not self.appear(RESEARCH_PENDING, offset=(20, 20)):
            logger.info('No research finished or pending')
            return False

        self.ui_ensure_research()
        self.research_reward()

        self.ui_goto(page_reward, skip_first_screenshot=True)
        return True
