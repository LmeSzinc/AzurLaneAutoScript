import cv2
import numpy as np
from scipy import signal
import module.config.server as server

from module.base.timer import Timer
from module.base.utils import color_similarity_2d, random_rectangle_vector, rgb2gray
from module.config.deep import deep_get
from module.island.assets import *
from module.island.project_data import *
from module.island.project import IslandItem, IslandProduct, IslandProject
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
        logger.hr('Island Project', level=2)
        self.device.click_record_clear()
        self.interval_clear([ISLAND_MANAGEMENT_CHECK, PROJECT_COMPLETE,
                             GET_ITEMS_ISLAND, ROLE_SELECT_ENTER])
        received = False
        enter = True
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

            if enter and self.appear_then_click(ROLE_SELECT_ENTER, offset=(5, 5), interval=2):
                received = True
                self.interval_clear(GET_ITEMS_ISLAND)
                timeout.reset()
                continue

            if self.appear_then_click(PROJECT_COMPLETE, offset=(20, 20), interval=2):
                received = True
                enter = False
                self.interval_clear(GET_ITEMS_ISLAND)
                self.interval_reset(ROLE_SELECT_ENTER)
                timeout.reset()
                continue

            if self.appear_then_click(GET_ITEMS_ISLAND, offset=(20, 20), interval=2):
                enter = True
                self.interval_clear(ROLE_SELECT_ENTER)
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
        """
        Select a role to produce.
        """
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

    def island_current_product(self):
        """
        Get currently selected product on self.device.image.

        Returns:
            IslandItem: currently selected item
        """
        image = self.image_crop(ISLAND_PRODUCT_ITEMS, copy=False)
        y_top = ISLAND_PRODUCT_ITEMS.area[1]
        line = cv2.reduce(image, 1, cv2.REDUCE_AVG)
        # blue line
        line = color_similarity_2d(line, color=(57, 189, 255))[:, 0]
        parameters = {
            'height': 200,
            'distance': 50,
        }
        peaks, _ = signal.find_peaks(line, **parameters)
        peaks = np.array(peaks) + y_top
        return IslandItem(self.device.image, peaks)

    def island_select_product(self, option, skip_first_screenshot=True):
        """
        Select a product in items list.

        Args:
            option (str): option to select
            skip_first_screenshot (bool):
        """
        logger.hr('Island Select Product')
        last = None
        click_interval = Timer(1)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            current = self.island_current_product()

            if option == current.name:
                logger.info(f'Selected item {option}')
                return True

            drag = True
            for item in current.items:
                if option == item.name:
                    if click_interval.reached():
                        self.device.click(item.button)
                        self.device.sleep(0.2)
                        click_interval.reset()
                    drag = False
            
            if last == current.items[-1]:
                logger.info(f'Reach the bottom of items, dit not match item {option}')
                self.island_product_quit()
                return False

            if drag:
                last = current.items[-1]
                self.device.click(last.button)
                self.island_drag_next_page((0, -300), ISLAND_PRODUCT_ITEMS.area, 0.5)

    def island_product_confirm(self, skip_first_screenshot=True):
        """
        Start the product after product selected.

        Args:
            skip_first_screenshot (bool):
        """
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
            if self.image_color_count(PROJECT_START, color=(151, 155, 155), threshold=221, count=200):
                self.island_product_quit()
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

                if self.info_bar_count():
                    self.island_product_quit()
                    break
                if self.island_in_management():
                    break

    def island_drag_next_page(self, vector, box, sleep=0.5):
        """
        Drag to the next page.

        Args:
            vector (tuple):
            box (tuple):
            sleep (float):
        """
        p1, p2 = random_rectangle_vector(vector, box=box, random_range=(0, -5, 0, 5))
        self.device.drag(p1, p2, segments=2, shake=(0, 25), point_random=(0, 0, 0, 0), shake_random=(0, -5, 0, 5))
        self.device.sleep(sleep)

    def ensure_project(self, project: IslandProject, trial=7, skip_first_screenshot=True):
        logger.hr('Project ensure')
        for _ in range(trial):
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            projects = self.project_detect(self.device.image)
            if not projects:
                continue
            if project.name in projects.get('name'):
                break

            self.island_drag_next_page((0, -500), ISLAND_PROJECT_SWIPE.area, 0.6)

    def island_run(self, names, trial=2, skip_first_screenshot=True):
        """
        Execute island run to receive and start project.

        Args:
            names (bool):
            trial (int):
            skip_first_screenshot (bool):
        """
        logger.hr('Island Run', level=1)
        end = False
        timeout = Timer(3, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                break

            projects = self.project_detect(self.device.image)
            if trial > 0 and not projects:
                trial -= 1
                continue
            projects: SelectedGrids = projects.filter(
                lambda proj: proj.name in names and proj.name not in self.project.get('name'))
            self.project = self.project.add_by_eq(projects)

            for proj in projects:
                if proj.name == names[-1]:
                    end = True
                proj_config = self.island_project_config(proj)

                for button, option, index in zip(
                        proj.slot_buttons.buttons, proj_config, range(len(proj_config))):
                    if option is None:
                        continue
                    if self.project_receive(button):
                        self.island_select_role()
                        if self.island_select_product(option):
                            self.island_product_confirm()
                        if not end or index != len(proj_config) - 1:
                            self.ensure_project(proj)
                timeout.reset()

            if end:
                break
            self.island_drag_next_page((0, -500), ISLAND_PROJECT_SWIPE.area, 0.6)

        # task delay
        future_finish = sorted([f for f in self.total.get('finish_time') if f is not None])
        logger.info(f'Project finish: {[str(f) for f in future_finish]}')
        if len(future_finish):
            self.config.task_delay(target=future_finish)
        else:
            logger.info('No island project running')
            self.config.task_delay(success=False)

    def island_project_config(self, project: IslandProject):
        """
        Args:
            project (IslandProject):
        
        Returns:
            list[str]: a list of options for production
        """
        slot_option = []
        proj_id = project.id
        for proj_slot in range(1, project.slot + 1):
            option = self.config.__getattribute__(f'Island{proj_id}_Option{proj_slot}')
            if option == 0:
                slot_option.append(None)
                continue
            slot_option.append(deep_get(items_data_cn, [proj_id, option]))
        return slot_option

    @staticmethod
    def island_config_to_names(config):
        """
        Args:
            config (list[bool]): list of config for island receive
        
        Returns:
            list[str]: a list of name for island receive
        """
        if any(config):
            return [name for add, name in zip(config, list(name_to_slot_cn.keys())) if add]
        else:
            return []

    def run(self):
        if server.server in ['cn']:
            names = self.island_config_to_names(
                [self.config.__getattribute__(f'Island{i}_Receive') for i in range(1, 16)])
            if len(names):
                self.ui_ensure(page_dormmenu)
                self.ui_goto(page_island, get_ship=False)
                self.device.sleep(0.5)
                self.ui_ensure(page_island_phone)
                self.island_management_enter()
                self.island_run(names=names)
                self.island_management_quit()
                self.ui_goto(page_main, get_ship=False)
            else:
                logger.info('Nothing to receive, skip island running')
                self.config.task_delay(server_update=True)
        else:
            logger.info(f'Island task not presently supported for {server.server} server.')
            logger.info('If want to address, review necessary assets, replace, update above condition, and test')
            self.config.task_delay(server_update=True)
