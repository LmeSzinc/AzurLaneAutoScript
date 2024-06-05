from module.base.timer import Timer
from module.base.utils import crop, rgb2gray
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2, GET_ITEMS_3, GET_ITEMS_3_CHECK
from module.logger import logger
from module.research.assets import *
from module.research.project import RESEARCH_STATUS
from module.research.series import RESEARCH_SCALING
from module.ui.assets import RESEARCH_CHECK
from module.ui.ui import UI


class ResearchUI(UI):
    def is_in_research(self):
        return self.appear(RESEARCH_CHECK, offset=(20, 20))

    def is_in_queue(self):
        return self.appear(QUEUE_CHECK, offset=(20, 20))

    def ensure_research_stable(self):
        self.wait_until_stable(STABLE_CHECKER)

    def ensure_research_center_stable(self):
        self.wait_until_stable(STABLE_CHECKER_CENTER)

    def queue_enter(self, skip_first_screenshot=True):
        """
        Pages:
            in: is_in_research
            out: is_in_queue
        """
        self.ui_click(RESEARCH_GOTO_QUEUE, check_button=self.is_in_queue, appear_button=self.is_in_research,
                      retry_wait=1, skip_first_screenshot=skip_first_screenshot)

    def queue_quit(self, skip_first_screenshot=True):
        """
        Pages:
            in: is_in_queue
            out: is_in_research, project stabled
        """
        self.ui_back(check_button=self.is_in_research, appear_button=self.is_in_queue,
                     retry_wait=3, skip_first_screenshot=skip_first_screenshot)
        self.ensure_research_center_stable()

    def get_items(self):
        """
        Returns:
            Button:
        """
        if self.appear(GET_ITEMS_3, offset=(5, 5)):
            if self.image_color_count(GET_ITEMS_3_CHECK, color=(255, 255, 255), threshold=221, count=100):
                return GET_ITEMS_3
            else:
                return GET_ITEMS_2
        if self.appear(GET_ITEMS_1, offset=(5, 5)):
            return GET_ITEMS_1
        return None

    def drop_record(self, drop):
        """
        Args:
            drop (DropRecord):
        """
        if not drop:
            return
        button = self.get_items()
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

    def get_research_status(self, image):
        """
        Args:
            image: Screenshot

        Returns:
            list[str]: List of project status
        """
        out = []
        for index, status, scaling in zip(range(5), RESEARCH_STATUS, RESEARCH_SCALING):
            info = status.crop((0, -40, 200, 0))
            piece = rgb2gray(crop(image, info.area))
            if TEMPLATE_WAITING.match(piece, scaling=scaling, similarity=0.75):
                out.append('waiting')
            elif TEMPLATE_RUNNING.match(piece, scaling=scaling, similarity=0.75):
                out.append('running')
            elif TEMPLATE_DETAIL.match(piece, scaling=scaling, similarity=0.75):
                out.append('detail')
            else:
                out.append('unknown')

        logger.info(f'Research status: {out}')
        return out

    def is_research_stabled(self):
        return self.is_in_research() and 'detail' in self.get_research_status(self.device.image)

    def research_detail_quit(self, skip_first_screenshot=True):
        logger.info('Research detail quit')
        click_timer = Timer(10)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.is_research_stabled():
                break

            if self.appear(RESEARCH_UNAVAILABLE, offset=(20, 20)) \
                    or self.appear(RESEARCH_START, offset=(20, 20)) \
                    or self.appear(RESEARCH_STOP, offset=(20, 20)):
                if click_timer.reached():
                    self.device.click(RESEARCH_DETAIL_QUIT)
                    click_timer.reset()

    def research_detail_cancel(self, skip_first_screenshot=True):
        logger.info('Research detail cancel')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.is_research_stabled():
                break

            if self.appear_then_click(RESEARCH_STOP, offset=(20, 20), interval=5):
                continue
            if self.handle_popup_confirm('RESEARCH_CANCEL'):
                continue
            if self.appear(RESEARCH_START, offset=(20, 20), interval=5):
                self.device.click(RESEARCH_DETAIL_QUIT)
                continue
