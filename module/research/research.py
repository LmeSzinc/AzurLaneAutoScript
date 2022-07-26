import numpy as np
from datetime import datetime, timedelta

from module.base.timer import Timer
from module.base.utils import rgb2gray
from module.logger import logger
from module.ocr.ocr import Duration
from module.research.assets import *
from module.research.project import (RESEARCH_ENTRANCE, ResearchSelector,
                                     get_research_finished)
from module.research.rqueue import ResearchQueue
from module.ui.page import *

OCR_DURATION = Duration(RESEARCH_LAB_DURATION_REMAIN, letter=(255, 255, 255), threshold=64,
                        name='RESEARCH_LAB_DURATION_REMAIN')


class RewardResearch(ResearchSelector, ResearchQueue):
    _research_project_offset = 0
    _research_finished_index = 2
    research_project_started = None  # ResearchProject
    enforce = False
    end_time = None

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

    def research_enforce(self, drop=None, add_queue=True):
        """
        Args:
            drop (DropImage):
            add_queue (bool): Whether to add into queue.
                The 6th project can't be added into queue, so here's the toggle.
        """
        if not self.enforce:
            logger.info('Enforce choosing research project')
            self.enforce = True
            return self.research_select(self.research_sort_filter(self.enforce),
                                        drop=drop, add_queue=add_queue)
        return True

    def research_select(self, priority, drop=None, add_queue=True):
        """
        Args:
            priority (list): A list of ResearchProject objects and preset strings,
                such as [object, object, object, 'reset']
            drop (DropImage):
            add_queue (bool): Whether to add into queue.
                The 6th project can't be added into queue, so here's the toggle.

        Returns:
            bool: False if have been reset
        """
        if not len(priority):
            logger.info('No research project satisfies current filter')
            return self.research_enforce(drop=drop, add_queue=add_queue)
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
                    self.research_select(self.research_sort_shortest(self.enforce),
                                         drop=drop, add_queue=add_queue)
                elif project == 'cheapest':
                    self.research_select(self.research_sort_cheapest(self.enforce),
                                         drop=drop, add_queue=add_queue)
                else:
                    logger.warning(f'Unknown select method: {project}')
                return True
            elif project.genre.upper() in ['C', 'T'] and \
                    self.research_enforce(drop=drop, add_queue=add_queue):
                return True
            else:
                # priority example: [ResearchProject, ResearchProject,]
                ret = self.research_project_start(project, add_queue=add_queue)
                if ret:
                    return True
                elif ret is not None and self.research_delay_check():
                    logger.info('Delay research when resources not enough and queue not empty')
                    return True
                else:
                    continue

        logger.info('No research project started')
        return self.research_enforce(drop=drop, add_queue=add_queue)

    def research_delay_check(self):
        """
        Check whether the conditions allow the delay of research.

        Returns:
            bool: If conditions allow to delay research.
        """
        if self.config.Research_AllowDelay:
            slot = self.get_queue_slot()
            if slot < 4:
                return True
            if slot == 4:
                if self.end_time <= datetime.now():
                    return True
                elif self.end_time + timedelta(minutes=-10) > datetime.now():
                    return True

        return False

    def research_project_start(self, project, add_queue=True, skip_first_screenshot=True):
        """
        Start a given project and add it into research queue.

        Args:
            project (ResearchProject, int): Project or index of project 0 to 4.
            add_queue (bool): Whether to add into queue.
                The 6th project can't be added into queue, so here's the toggle.
            skip_first_screenshot:

        Returns:
            bool: If start success.
            None: If The project to start is not in known projects.

        Pages:
            in: is_in_research
            out: is_in_research
        """
        logger.hr('Research project start')
        logger.info(f'Research project: {project}')
        if isinstance(project, int):
            index = project
        elif project in self.projects:
            index = self.projects.index(project)
        else:
            logger.warning(f'The project to start: {project} is not in known projects')
            return None
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
                # RESEARCH_STOP is a semi-transparent button,
                # color will vary depending on the background.
                if add_queue:
                    self.research_queue_add()
                else:
                    self.research_detail_quit()
                # self.ensure_no_info_bar(timeout=3)  # Research started
                self.research_project_started = project
                return True
            if not available and max_rgb <= 235 \
                    and self.appear(RESEARCH_UNAVAILABLE, offset=(5, 20)):
                logger.info('Not enough resources to start this project')
                self.research_detail_quit()
                self.research_project_started = None
                return False

    def research_receive(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Pages:
            in: page_research, stable, with project finished.
            out: page_research

        Returns:
            bool: True if success to receive rewards.
                  False if project requirements are not satisfied.
        """
        logger.hr('Research receive', level=3)
        with self.stat.new(
                genre='research', method=self.config.DropRecord_ResearchRecord
        ) as record:
            # Take screenshots of project list
            record.add(self.device.image)

            # Click finished project, to GET_ITEMS_*
            confirm_timer = Timer(1.5, count=5)
            record_button = None
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                if self.appear(RESEARCH_CHECK, interval=10):
                    if self.research_has_finished():
                        self.device.click(RESEARCH_ENTRANCE[self._research_finished_index])

                if self.appear(RESEARCH_STOP, offset=(20, 20)):
                    logger.info('The research time is up, but requirements are not satisfied')
                    self.research_project_started = None
                    self.research_detail_quit()
                    return False
                # Entered another project accidentally
                if self.appear(RESEARCH_START, offset=(20, 20), interval=5):
                    self.device.click(RESEARCH_DETAIL_QUIT)
                    continue

                appear_button = self.get_items()
                if appear_button is not None:
                    if appear_button == record_button:
                        if confirm_timer.reached():
                            break
                    else:
                        logger.info(f'{appear_button} appeared')
                        record_button = appear_button
                        confirm_timer.reset()

            # Take screenshots of items
            self.drop_record(drop=record)

        # Close GET_ITEMS_*, to project list
        self.ui_click(appear_button=self.get_items, click_button=GET_ITEMS_RESEARCH_SAVE,
                      check_button=self.is_in_research, skip_first_screenshot=True)
        return True

    def queue_receive(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Pages:
            in: is_in_queue
            out: is_in_queue

        Returns:
            int: Number of research project received
        """
        logger.hr('Queue receive', level=1)
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
                appear_button = self.get_items()
                if appear_button is not None:
                    if appear_button == record_button:
                        if item_confirm.reached():
                            # Record drops and close get items
                            self.drop_record(drop=record)
                            self.device.click(GET_ITEMS_RESEARCH_SAVE)
                            item_confirm.reset()
                            record_button = None
                            total += 1
                            continue
                    else:
                        logger.info(f'{appear_button} appeared')
                        record_button = appear_button
                        item_confirm.reset()
                else:
                    item_confirm.reset()
                    record_button = None

                # Claim rewards
                if self.appear_then_click(QUEUE_CLAIM_REWARD, offset=None, interval=5):
                    continue

            if total <= 0:
                record.clear()

        logger.info(f'Received rewards from {total} projects')
        return total

    def queue_quit(self, *args, **kwargs):
        super().queue_quit(*args, **kwargs)
        self._research_project_offset = 0

    def research_queue_append(self, drop=None, add_queue=True):
        """
        Args:
            drop (DropImage):
            add_queue (bool): Whether to add into queue.
                The 6th project can't be added into queue, so here's the toggle.

        Returns:
            bool: If success to start a project
        """
        self.research_project_started = None
        project_record = None
        for _ in range(2):
            logger.hr('Research select', level=2)
            self._research_project_offset = 0
            # Handle info bar, take one more screenshot to wait the remains of info_bar
            if self.handle_info_bar():
                self.device.screenshot()
            self.research_detect()
            project_record = self.device.image
            priority = self.research_sort_filter()
            result = self.research_select(priority, drop=drop, add_queue=add_queue)
            if result:
                break

        if self.research_project_started is not None:
            if project_record is not None:
                drop.add(project_record)
            return True
        else:
            return False

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
                        logger.info(f'Unable to start a project, stop filling queue, queue added: {total}')
                        return total
                else:
                    break

            # Run the 6th project
            status = self.get_research_status(self.device.image)
            if 'waiting' not in status:
                logger.info('Select the 6th research')
                self.research_queue_append(drop=drop, add_queue=False)
            else:
                logger.info('6th research already waiting')

            logger.info(f'Research queue full filled, queue added: {total}')
            return total

    def receive_6th_research(self):
        """
        Returns:
            bool: If success
        """
        logger.hr('Receive 6th research', level=2)
        # Check if it's finished
        if self.research_has_finished():
            logger.info(f'6th research finished at: {self._research_finished_index}')
            success = self.research_receive()
            if not success:
                return False
        else:
            logger.info('No research has finished')
        # Check if it's waiting or running
        status = self.get_research_status(self.device.image)
        if 'waiting' in status:
            if self.get_queue_slot() > 0:
                self.research_project_start(status.index('waiting'))
            else:
                logger.info('Queue full, stop appending waiting research')
        if 'running' in status:
            if self.get_queue_slot() > 0:
                self.research_project_start(status.index('running'))
            else:
                logger.info('Queue full, stop appending running research')

        return True

    def run(self):
        """
        Pages:
            in: Any page
            out: page_research, with research project information, but it's still page_research.
                    or page_main
        """
        self.ui_ensure(page_research)

        # Check queue
        self.queue_enter()
        self.queue_receive()
        self.end_time = self.get_research_ended()
        self.queue_quit()

        # Check the 6th project, which is outside of queue
        self.receive_6th_research()

        # Fill queue
        total = self.research_fill_queue()

        # Scheduler
        if self.end_time <= datetime.now() and total == 0:
            # Queue empty, can't start any research
            self.config.task_delay(server_update=True)
            return
        elif self.end_time <= datetime.now() and total > 0:
            # Get the remain of project newly started
            self.queue_enter()
            self.end_time = self.get_research_ended()
            self.queue_quit()
        if self.get_queue_slot() == 4:
            # Queue nearly empty, give up research because of resources not enough,
            # ten minutes in advance to avoid idle research.
            self.end_time = self.end_time + timedelta(minutes=-10)
        self.config.task_delay(target=self.end_time)
