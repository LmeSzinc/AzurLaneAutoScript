from module.base.button import ButtonGrid
from module.base.decorator import cached_property, Config
from module.logger import logger
from module.ocr.ocr import Duration
from module.research.assets import *
from module.research.ui import ResearchUI

OCR_QUEUE_REMAIN = Duration(QUEUE_REMAIN, letter=(255, 255, 255), threshold=128, name='OCR_QUEUE_REMAIN')


class ResearchQueue(ResearchUI):
    def research_queue_add(self, skip_first_screenshot=True):
        """
        Pages:
            in: RESEARCH_QUEUE_ADD (is_in_research, DETAIL_NEXT)
            out: is_in_research and stabled
        """
        logger.hr('Research queue add')
        # POPUP_CONFIRM has just been clicked in research_project_start()
        self.popup_interval_clear()
        self.interval_clear([RESEARCH_QUEUE_ADD])
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(RESEARCH_QUEUE_ADD, offset=(20, 20), interval=3):
                continue
            if self.handle_popup_confirm('RESEARCH_QUEUE'):
                continue

            # End
            if self.is_in_research() and 'detail' in self.get_research_status(self.device.image):
                break

        self.ensure_research_center_stable()

    @cached_property
    @Config.when(SERVER='en')
    def queue_status_grids(self):
        """
        Status icons on the left
        """
        return ButtonGrid(
            origin=(8, 259), delta=(0, 40.5), button_shape=(25, 25), grid_shape=(1, 5), name='QUEUE_STATUS')

    @cached_property
    @Config.when(SERVER='jp')
    def queue_status_grids(self):
        """
        Status icons on the left
        """
        return ButtonGrid(
            origin=(8, 259), delta=(0, 40.5), button_shape=(25, 25), grid_shape=(1, 5), name='QUEUE_STATUS')

    @cached_property
    @Config.when(SERVER=None)
    def queue_status_grids(self):
        """
        Status icons on the left
        """
        return ButtonGrid(
            origin=(18, 259), delta=(0, 40.5), button_shape=(25, 25), grid_shape=(1, 5), name='QUEUE_STATUS')

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

    def get_queue_slot(self):
        """
        Returns:
            int: Number of empty slots in queue

        Pages:
            in: is_in_queue
        """
        status = [self._queue_status_detect(button) for button in self.queue_status_grids.buttons]
        logger.info(f'Research queue: {status}')
        slot = sum([int(s == 'empty') for s in status])
        logger.attr('Research queue slot', slot)
        return slot

    def get_queue_remain(self):
        """
        Returns:
            int: Seconds before research finished

        Pages:
            in: is_in_queue
        """
        if not self.image_color_count(QUEUE_REMAIN, color=(255, 255, 255), threshold=221, count=100):
            logger.info('Research queue empty')
            return 0

        remain = OCR_QUEUE_REMAIN.ocr(self.device.image)
        logger.info(f'Research queue remain: {remain}')
        return remain.total_seconds()
