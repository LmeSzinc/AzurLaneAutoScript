import numpy as np

from module.base.timer import Timer
from module.base.utils import rgb2gray
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2, GET_ITEMS_3, GET_ITEMS_3_CHECK
from module.logger import logger
from module.ocr.ocr import Duration
from module.research.assets import *
from module.research.project import (RESEARCH_ENTRANCE, ResearchProject,
                                     ResearchSelector)
from module.research.rqueue import ResearchQueue
from module.ui.page import *

OCR_DURATION = Duration(RESEARCH_LAB_DURATION_REMAIN, letter=(255, 255, 255), threshold=64,
                        name='RESEARCH_LAB_DURATION_REMAIN')


class RewardResearch(ResearchSelector, ResearchQueue):
    _research_project_offset = 0
    research_project_started = None  # ResearchProject
    enforce = False

    def ensure_research_stable(self):
        self.wait_until_stable(STABLE_CHECKER)

    def research_reset(self, drop=None, skip_first_screenshot=True):
        """
        Args:
            drop (DropImage):
            skip_first_screenshot (bool):

        Returns:
            bool: If reset success.
        """
        if not self.appear(RESET_AVAILABLE):
            logger.info('Research reset unavailable')
            return False

        logger.info('Research reset')
        drop.add(self.device.image)
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
            if executed and self.is_in_research():
                self.ensure_no_info_bar(timeout=3)  # Refresh success
                self.ensure_research_stable()
                break

        self._research_project_offset = 0
        return True

    def research_enforce(self):
        """
        Returns:
            bool: True if triggered enforce research
        """
        if (not self.enforce) \
                and (self.config.Research_UseCube in ['only_no_project', 'only_05_hour']
                     or self.config.Research_UseCoin in ['only_no_project', 'only_05_hour']
                     or self.config.Research_UsePart in ['only_no_project', 'only_05_hour']):
            logger.info('Enforce choosing research project')
            self.enforce = True
            self.research_select(self.research_sort_filter(self.enforce))
            return True
        return False

    def research_select(self, priority, drop=None):
        """
        Args:
            priority (list): A list of ResearchProject objects and preset strings,
                such as [object, object, object, 'reset']
            drop (DropImage):

        Returns:
            bool: False if have been reset
        """
        if not len(priority):
            logger.info('No research project satisfies current filter')
            self.research_enforce()
            return True
        for project in priority:
            # priority example: ['reset', 'shortest']
            if project == 'reset':
                if self.research_reset(drop=drop):
                    return False
                else:
                    continue

            if isinstance(project, str):
                # priority example: ['shortest']
                if project == 'shortest':
                    self.research_select(self.research_sort_shortest(self.enforce), drop=drop)
                elif project == 'cheapest':
                    self.research_select(self.research_sort_cheapest(self.enforce), drop=drop)
                else:
                    logger.warning(f'Unknown select method: {project}')
                return True
            elif project.genre.upper() in ['C', 'T'] and self.research_enforce():
                return True
            else:
                # priority example: [ResearchProject, ResearchProject,]
                if self.research_project_start(project):
                    return True
                else:
                    continue

        logger.info('No research project started')
        self.research_enforce()
        return True

    def research_project_start(self, project, skip_first_screenshot=True):
        """
        Start a given project and add it into research queue.

        Args:
            project (ResearchProject):
            skip_first_screenshot:

        Returns:
            bool: If start success.

        Pages:
            in: is_in_research
            out: is_in_research
        """
        logger.info(f'Research project: {project}')
        if project in self.projects:
            index = self.projects.index(project)
        else:
            logger.warning(f'The project to start: {project} is not in known projects')
            return False
        logger.info(f'Research project: {index}')
        self.interval_clear([RESEARCH_START])
        self.popup_interval_clear()
        available = False
        click_timer = Timer(10)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            max_rgb = np.max(rgb2gray(self.image_crop(RESEARCH_UNAVAILABLE)))

            # Don't use interval here, RESEARCH_CHECK already appeared 5 seconds ago
            if click_timer.reached() and self.is_in_research():
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
                self.research_queue_add()
                # self.ensure_no_info_bar(timeout=3)  # Research started
                self.research_project_started = project
                return True
            if not available and max_rgb <= 235 and self.appear(RESEARCH_UNAVAILABLE, offset=(5, 20)):
                logger.info('Not enough resources to start this project')
                self.research_detail_quit()
                self.research_project_started = None
                return False

    def research_receive(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Pages:
            in: is_in_queue
            out: is_in_queue

        Returns:
            int: Number of research project received
        """
        logger.hr('Research receive', level=1)

        def get_items():
            if self.appear(GET_ITEMS_3, offset=(5, 5)):
                if self.image_color_count(GET_ITEMS_3_CHECK, color=(255, 255, 255), threshold=221, count=100):
                    return GET_ITEMS_3
                else:
                    return GET_ITEMS_2
            if self.appear(GET_ITEMS_1, offset=(5, 5)):
                return GET_ITEMS_1
            return None

        def drop_record(drop):
            if not drop:
                return
            button = get_items()
            if button == GET_ITEMS_1 or button == GET_ITEMS_2:
                drop.add(self.device.image)
            elif button == GET_ITEMS_3:
                self.device.sleep(1.5)
                self.device.screenshot()
                drop.add(self.device.image)
                self.device.swipe_vector((0, 250), box=ITEMS_3_SWIPE.area, random_range=(-10, -10, 10, 10),
                                         padding=0)
                self.device.sleep(2)
                self.device.screenshot()
                drop.add(self.device.image)

        total = 0
        with self.stat.new(
                genre='research', method=self.config.DropRecord_ResearchRecord
        ) as record:
            # Take screenshots of project list
            record.add(self.device.image)

            end_confirm = Timer(1, count=3)
            item_confirm = Timer(1.5, count=5)
            record_button = None
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                # End
                # No offset, color detection only
                if self.is_in_queue() and not self.appear(QUEUE_CLAIM_REWARD, offset=None):
                    if end_confirm.reached():
                        break
                else:
                    end_confirm.reset()

                # Get items
                appear_button = get_items()
                if appear_button is not None:
                    if appear_button == record_button:
                        if item_confirm.reached():
                            # Record drops and close get items
                            drop_record(record)
                            self.device.click(GET_ITEMS_RESEARCH_SAVE)
                            item_confirm.reset()
                            total += 1
                            continue
                    else:
                        logger.info(f'{appear_button} appeared')
                        record_button = appear_button
                        item_confirm.reset()
                else:
                    item_confirm.reset()

                # Claim rewards
                if self.appear_then_click(QUEUE_CLAIM_REWARD, offset=None, interval=5):
                    continue

            if total <= 0:
                record.clear()

        logger.info(f'Received rewards from {total} projects')
        return total

    def research_queue_append(self, drop=None):
        """
        Args:
            drop (DropImage):

        Returns:
            bool: If success to start a project
        """
        self.research_project_started = None
        for _ in range(2):
            logger.hr('Research select', level=2)
            self._research_project_offset = 0
            # Handle info bar, take one more screenshot to wait the remains of info_bar
            if self.handle_info_bar():
                self.device.screenshot()
            self.research_detect()
            drop.add(self.device.image)
            priority = self.research_sort_filter()
            result = self.research_select(priority, drop=drop)
            if result:
                break

        return self.research_project_started is not None

    def research_fill_queue(self):
        """
        Select researches until queue full filled

        Returns:
            int: Number of queued researches

        Pages:
            in: is_in_research
        """
        logger.hr('Research fill queue', level=1)
        total = 0
        with self.stat.new(
                genre='research', method=self.config.DropRecord_ResearchRecord
        ) as drop:
            for _ in range(5):
                if self.get_queue_slot() > 0:
                    success = self.research_queue_append(drop=drop)
                    if success:
                        total += 1
                    else:
                        return total
                else:
                    logger.info(f'Research queue full filled, queue added: {total}')
                    return total

    def run(self):
        """
        Pages:
            in: Any page
            out: page_research, with research project information, but it's still page_research.
                    or page_main
        """
        # Remove this when your server is updated for PR5
        if self.config.SERVER in ['en', 'jp', 'tw']:
            logger.warning('Task "Research" is forced delayed 2 hours before PR5 support. '
                           'Please do research manually and contact server maintainers')
            self.config.task_delay(minute=120)
            self.config.task_stop()

        self.ui_ensure(page_research)
        self.queue_enter()
        self.research_receive()
        remain = self.get_queue_remain()
        self.queue_quit()
        total = self.research_fill_queue()

        if remain > 0:
            self.config.task_delay(minute=remain / 60)
        elif total > 0:
            # Get the remain of project newly started
            self.queue_enter()
            remain = self.get_queue_remain()
            self.queue_quit()
            self.config.task_delay(minute=remain / 60)
        else:
            # Queue empty, can't start any research
            self.config.task_delay(server_update=True)
