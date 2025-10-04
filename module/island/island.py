import module.config.server as server

from module.base.timer import Timer
from module.base.utils import rgb2gray
from module.island.assets import *
from module.island.project import IslandProduct, IslandProject
from module.island.ui import IslandUI
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.ui.page import page_dormmenu, page_island, page_island_phone, page_main


class Island(IslandUI):
    project = SelectedGrids([])
    total = SelectedGrids([])

    def project_detect(self, image):
        """
        Get all projects from an image.

        Args:
            image (np.ndarray):

        Returns:
            SelectedGrids:
        """
        image_gray = rgb2gray(image)
        projects = SelectedGrids([IslandProject(image, image_gray, button)
                                  for button in TEMPLATE_ISLAND_SWITCH.match_multi(image_gray)])
        return projects.select(valid=True)

    def project_receive(self, button, skip_first_screenshot=True):
        """
        Receive and start a project.

        Args:
            button (Button):

        Returns:
            bool: if received.
        """
        self.interval_clear([ISLAND_MANAGEMENT_CHECK, PROJECT_COMPLETE,
                             GET_ITEMS_ISLAND, ROLE_SELECT_ENTER])
        received = False
        timeout = Timer(3, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.island_in_management(interval=5):
                self.device.click(button)
                timeout.reset()
                continue

            if self.handle_info_bar():
                timeout.reset()
                continue

            if self.appear_then_click(PROJECT_COMPLETE, offset=(20, 20), interval=2):
                received = True
                self.interval_clear(GET_ITEMS_ISLAND)
                self.interval_reset(ROLE_SELECT_ENTER)
                timeout.reset()
                continue

            if self.appear_then_click(GET_ITEMS_ISLAND, offset=(20, 20), interval=2):
                self.interval_clear(ROLE_SELECT_ENTER)
                timeout.reset()
                continue

            if self.appear_then_click(ROLE_SELECT_ENTER, offset=(5, 5), interval=2):
                received = True
                self.interval_clear(GET_ITEMS_ISLAND)
                timeout.reset()
                continue

            if self.appear(ROLE_SELECT_CONFIRM, offset=(20, 20)):
                break
            if timeout.reached():
                break

            if not received:
                product = IslandProduct(self.device.image)
                if product.valid:
                    self.total = self.total.add_by_eq(SelectedGrids([product]))
                    self.device.click(ISLAND_CLICK_SAFE_AREA)
                    break
                else:
                    self.interval_clear(ROLE_SELECT_ENTER)

        return received

    def island_select_manjuu(self, button):
        self.interval_clear([ROLE_SELECT_CONFIRM, ISLAND_AMOUNT_MAX])
        for _ in self.loop():
            if self.appear(ROLE_SELECT_CHECK, offset=(20, 20)):
                break

            if self.appear(ROLE_SELECT_CONFIRM, offset=(20, 20), interval=5):
                self.device.click(button)
                continue

        self.ui_click(
            click_button=ROLE_SELECT_CONFIRM,
            check_button=ISLAND_AMOUNT_MAX,
            offset=(20, 20),
            retry_wait=3,
            skip_first_screenshot=True
        )

    def island_select_role(self, skip_first_screenshot=True):
        timeout = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                break

            image = self.image_crop((0, 0, 910, 1280), copy=False)
            sim, button = TEMPLATE_ISLAND_MANJUU.match_result(image)
            if sim > 0.9:
                self.island_select_manjuu(button)
                break
            else:
                logger.info('No manjuu found')
                continue

    def island_select_product(self, skip_first_screenshot=True):
        last = None
        success = False
        timeout = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                break

            if not success:
                if self.appear_then_click(ISLAND_AMOUNT_MAX, offset=(5, 5), interval=5):
                    timeout.reset()
                    continue

                product = IslandProduct(self.device.image, new=True)
                if product == last:
                    success = True
                    self.total = self.total.add_by_eq(SelectedGrids([product]))
                    timeout.reset()
                    continue
                last = product
            else:
                if self.appear_then_click(PROJECT_START, offset=(20,20), interval=2):
                    timeout.reset()
                    self.interval_reset(ISLAND_MANAGEMENT_CHECK)
                    continue

                if self.appear(PROJECT_STAR_NOT_SATISFIED, offset=(20,20)):
                    self.island_product_quit()
                    break
                if self.info_bar_count():
                    self.island_product_quit()
                    break
                if self.island_in_management():
                    break

    def island_run(self, names, skip_first_screenshot=True):
        """
        Execute island run to receive and start project.

        Args:
            names (bool):
            skip_first_screenshot (bool):
        """
        logger.hr('Island Run', level=1)
        names = self.island_config_to_names(names)
        success = False
        timeout = Timer(3, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                break

            projects = self.project_detect(self.device.image)
            projects = projects.filter(lambda proj: proj.name in names and proj.name not in self.project.get('name'))
            self.project = self.project.add_by_eq(projects)

            for proj in projects:
                for button in proj.slot_buttons.buttons:
                    if self.project_receive(button):
                        self.island_select_role()
                        self.island_select_product()
                    success = True
                timeout.reset()

            if success:
                break

        future_finish = sorted([f for f in self.total.get('finish_time') if f is not None])
        logger.info(f'Project finish: {[str(f) for f in future_finish]}')
        if len(future_finish):
            self.config.task_delay(target=future_finish)
        else:
            logger.info('No island project running')
            self.config.task_delay(success=False)

    @staticmethod
    def island_config_to_names(config):
        if config:
            return ['沉石矿山', '翠土林场']
        else:
            return []

    def run(self):
        if server.server in ['cn']:
            if self.config.Island_ReceiveMiningForaging:
                self.ui_ensure(page_dormmenu)
                self.ui_goto(page_island, get_ship=False)
                self.device.sleep(0.5)
                self.ui_ensure(page_island_phone)
                self.island_management_enter()
                self.island_run(names=self.config.Island_ReceiveMiningForaging)
                self.island_management_quit()
                self.ui_goto(page_main, get_ship=False)
            else:
                logger.info('Nothing to receive, skip island running')
                self.config.task_delay(server_update=True)
        else:
            logger.info(f'Island task not presently supported for {server.server} server.')
            logger.info('If want to address, review necessary assets, replace, update above condition, and test')
            self.config.task_delay(server_update=True)
