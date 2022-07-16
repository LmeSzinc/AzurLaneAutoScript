from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.logger import logger
from module.research.assets import *
from module.ui.assets import RESEARCH_CHECK
from module.ui.ui import UI


class ResearchQueue(UI):
    def is_in_research(self):
        return self.appear(RESEARCH_CHECK, offset=(20, 20))

    def is_in_queue(self):
        return self.appear(QUEUE_CHECK, offset=(20, 20))

    def queue_enter(self, skip_first_screenshot=True):
        """
        Pages:
            in: is_in_research
            out: is_in_queue
        """
        self.ui_click(RESEARCH_GOTO_QUEUE, check_button=self.is_in_queue, appear_button=self.is_in_research,
                      retry_wait=3, skip_first_screenshot=skip_first_screenshot)

    def queue_quit(self, skip_first_screenshot=True):
        """
        Pages:
            in: is_in_queue
            out: is_in_research, project stabled
        """
        self.ui_back(check_button=self.is_in_research, appear_button=self.is_in_queue,
                     retry_wait=3, skip_first_screenshot=skip_first_screenshot)
        self.wait_until_stable(STABLE_CHECKER_CENTER)

    def research_queue_add(self, skip_first_screenshot=True):
        """
        Pages:
            in: RESEARCH_QUEUE_ADD (is_in_research, DETAIL_NEXT)
            out: is_in_research and stabled
        """
        logger.info('Research queue add')
        confirm_timer = Timer(0.3, count=1)
        # POPUP_CONFIRM has just been clicked in research_project_start()
        self.popup_interval_clear()
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

    @cached_property
    def queue_status_grids(self):
        """
        Status icons on the left
        """
        return ButtonGrid(
            origin=(8, 259), delta=(0, 40.5), button_shape=(25, 25), grid_shape=(1, 5), name='QUEUE_STATUS')

    def _queue_status_detect(self, button):
        """
        Args:
            button: Button of status icon

        Returns:
            str:
                'finished': Orange ✓ surrounded by orange border
                'running': Black ✓ surrounded by research progress, gray and blue
                'waiting': Gray … surrounded by gray border
                'empty': Black … surrounded by black border or just nothing
        """
        center = button.crop((7, 7, 21, 21))
        if self.image_color_count(center, color=(255, 158, 57), threshold=180, count=20):
            return 'finished'
        if self.image_color_count(center, color=(90, 97, 132), threshold=221, count=20):
            return 'waiting'
        if self.image_color_count(center, color=(24, 24, 41), threshold=221, count=10):
            below = button.crop((7, 14, 21, 21))
            if self.image_color_count(below, color=(24, 24, 41), threshold=221, count=10):
                return 'running'
            else:
                return 'empty'
        logger.warning(f'Unknown queue status from {button}, assume running')
        return 'running'

    def get_queue_remain(self):
        """
        Returns:
            int: Number of empty slots in queue

        Pages:
            in: is_in_queue
        """
        status = [self._queue_status_detect(button) for button in self.queue_status_grids.buttons]
        logger.info(f'Research queue: {status}')
        remain = sum([int(s == 'empty') for s in status])
        logger.attr('Research queue remain', remain)
        return remain
