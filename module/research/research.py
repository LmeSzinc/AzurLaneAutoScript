import numpy as np

from module.base.timer import Timer
from module.base.utils import rgb2gray
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2, GET_ITEMS_3
from module.logger import logger
from module.research.assets import *
from module.research.project import ResearchSelector, RESEARCH_ENTRANCE, get_research_finished
from module.ui.page import *


class RewardResearch(ResearchSelector):
    _research_project_offset = 0
    _research_finished_index = 2

    def ensure_research_stable(self):
        self.wait_until_stable(STABLE_CHECKER)

    def _in_research(self):
        return self.appear(RESEARCH_CHECK, offset=(20, 20))

    def _research_has_finished_at(self, index):
        """
        Args:
            index (int): Index of research project, 0 to 4

        Returns:
            bool: True if a research finished
        """
        finish = get_research_finished(self.device.image)
        return finish == index

    def research_has_finished(self):
        """
        Finished research should be auto-focused to the center, but sometimes didn't, due to an unknown game bug.
        This method will handle that.

        Returns:
            bool: True if a research finished
        """
        index = get_research_finished(self.device.image)
        if index is not None:
            logger.attr('Research_finished', index)
            self._research_finished_index = index
            return True
        else:
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

        self._research_project_offset = 0
        return True

    def research_select(self, priority, save_get_items=False):
        """
        Args:
            priority (list): A list of ResearchProject objects and preset strings,
                such as [object, object, object, 'reset']
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
                # priority example: [ResearchProject, ResearchProject,]
                if self.research_project_start(project):
                    return True
                else:
                    continue

        logger.info('No research project started')
        return True

    research_project_started = None

    def research_project_start(self, project, skip_first_screenshot=True):
        """
        Args:
            project (ResearchProject):
            skip_first_screenshot:

        Returns:
            bool: If start success.
        """
        logger.info(f'Research project: {project}')
        if project in self.projects:
            index = self.projects.index(project)
        else:
            logger.warning(f'The project to start: {project} is not in known projects')
            return False
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
                # self.ensure_no_info_bar(timeout=3)  # Research started
                self.research_project_started = project
                return True
            if not available and max_rgb <= 235 and self.appear(RESEARCH_UNAVAILABLE, offset=(5, 20)):
                logger.info('Not enough resources to start this project')
                self.research_detail_quit()
                self.research_project_started = None
                return False

    def research_receive(self, skip_first_screenshot=True, save_get_items=False):
        """
        Args:
            skip_first_screenshot:
            save_get_items:

        Pages:
            in: page_research, stable, with project finished.
            out: page_research
        """
        logger.info('Research receive')

        def get_items():
            for b in [GET_ITEMS_3, GET_ITEMS_2, GET_ITEMS_1]:
                if self.appear(b, offset=(5, 0)):
                    return b
            return None

        # Take screenshots of project list
        if save_get_items:
            self.device.save_screenshot('research_project', interval=0, to_base_folder=True)
        self.stat.add(self.device.image)

        # Click finished project, to GET_ITEMS_*
        confirm_timer = Timer(1.5, count=5)
        record_button = None
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(RESEARCH_CHECK, interval=10):
                if self._research_has_finished_at(self._research_finished_index):
                    self.device.click(RESEARCH_ENTRANCE[self._research_finished_index])

            appear_button = get_items()
            if appear_button is not None:
                if appear_button == record_button:
                    if confirm_timer.reached():
                        break
                else:
                    logger.info(f'{appear_button} appeared')
                    record_button = appear_button
                    confirm_timer.reset()

        # Take screenshots of items
        button = get_items()
        if button == GET_ITEMS_1 or button == GET_ITEMS_2:
            if save_get_items:
                self.device.save_screenshot('research_items', to_base_folder=True)
            self.stat.add(self.device.image)
        elif button == GET_ITEMS_3:
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
        self.stat.clear()

        # Close GET_ITEMS_*, to project list
        self.ui_click(appear_button=get_items, click_button=GET_ITEMS_RESEARCH_SAVE, check_button=self._in_research,
                      skip_first_screenshot=True)

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

    def ui_ensure_research(self):
        """
        Pages:
            in: Any page
            out: page_research
        """
        self.ui_goto(page_research, skip_first_screenshot=True)
        self.device.send_notification('Research Start', 'Research receive')
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
