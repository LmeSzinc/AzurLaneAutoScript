from datetime import datetime, timedelta
import cv2
import re
import numpy as np
from scipy import signal

from module.base.button import Button, ButtonGrid
from module.base.timer import Timer
from module.base.utils import color_similarity_2d, crop, random_rectangle_vector, rgb2gray
from module.config.deep import deep_get, deep_values
from module.island.assets import *
from module.island.project_data import *
from module.island.ui import IslandUI
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.ocr.ocr import Duration, Ocr


class ProjectNameOcr(Ocr):
    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('主', '丰')
        result = re.sub(r'[^\u4e00-\u9fff]', '', result)
        return result


class IslandProject:
    # If success to parse project
    valid: bool
    # OCR result
    name: str
    # Project workplace id
    id: int
    # max slot that the workplace has
    max_slot: int
    # available slots that the workplace has
    slot: int
    # buttons of all available slots
    slot_buttons: ButtonGrid

    def __init__(self, image, image_gray, button):
        """
        Args:
            image:
            image_gray:
            button:
        """
        self.image = image
        self.image_gray = image_gray
        self.button = button
        self.x1, self.y1, self.x2, self.y2 = button.area
        self.valid = True
        self.project_parse()

    def project_parse(self):
        # invalid
        if self.y2 + 110 >= 653:
            self.valid = False
            return

        # locked
        area = (self.x1 - 228, self.y1 + 57, self.x1 - 195, self.y1 + 95)
        image = crop(self.image_gray, area, copy=False)
        if TEMPLATE_PROJECT_LOCKED.match(image):
            self.valid = False
            return

        # name
        area = (self.x1 - 446, self.y1, self.x1 - 326, self.y2)
        button = Button(area=area, color=(), button=area, name='PROJECT_NAME')
        ocr = ProjectNameOcr(button, lang='cnocr')
        self.name = ocr.ocr(self.image)
        if not self.name:
            self.valid = False
            return

        # id
        keys = list(name_to_slot_cn.keys())
        if self.name in keys:
            self.id = keys.index(self.name) + 1
        else:
            self.valid = False
            return

        # max slot
        self.max_slot = name_to_slot_cn.get(self.name, 2)

        # available slot
        area = (self.x1 - 383, self.y1 + 60, self.x1 - 39, self.y1 + 118)
        image = crop(self.image_gray, area, copy=False)
        locked = TEMPLATE_SLOT_LOCKED.match_multi(image)
        self.slot = self.max_slot - len(locked)
        if not self.slot:
            self.valid = False
            return

        # slot grids
        self.slot_buttons = ButtonGrid(origin=(self.x1 - 383, self.y1 + 60), delta=(95, 0),
                                       button_shape=(58, 58), grid_shape=(self.slot, 1), name='PROJECT_SLOT')

    def __eq__(self, other):
        """
        Args:
            other (IslandProject):

        Returns:
            bool:
        """
        if not isinstance(other, IslandProject):
            return False
        if not self.valid or not other.valid:
            return False
        if self.name != other.name:
            return False
        if self.id != other.id:
            return False

        return True

    def __str__(self):
        return self.name


class IslandProduct:
    # Duration to run this product
    duration: timedelta
    # If success to parse product duration
    valid: bool

    def __init__(self, image, offset=None, new=False):
        if new:
            button = OCR_PRODUCTION_TIME
            if offset:
                button = OCR_PRODUCTION_TIME.move(offset)
            ocr = Duration(button, lang='cnocr', name='OCR_PRODUCTION_TIME')
            self.duration = ocr.ocr(image)
        else:
            ocr = Duration(OCR_PRODUCTION_TIME_REMAIN, name='OCR_PRODUCTION_TIME_REMAIN')
            self.duration = ocr.ocr(image)
        self.valid = True

        if not self.duration.total_seconds():
            self.valid = False

        self.create_time = datetime.now()

    @property
    def finish_time(self):
        if self.valid:
            return (self.create_time + self.duration).replace(microsecond=0)
        else:
            return None

    def __eq__(self, other):
        """
        Args:
            other (IslandProduct):

        Returns:
            bool:
        """
        if not isinstance(other, IslandProduct):
            return False
        threshold = timedelta(seconds=120)
        if not self.valid or not other.valid:
            return False
        if (other.duration < self.duration - threshold) or (other.duration > self.duration + threshold):
            return False

        return True


class ItemNameOcr(Ocr):
    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('蛮', '蜜').replace('茉', '末').replace('汗', '汁').replace('纠', '组')
        result = re.sub(r'[^\u4e00-\u9fff]', '', result)
        if '冰咖' in result:
            result = '冰咖啡'
        if '莓果香橙' in result:
            result = '莓果香橙甜点组'
        return result


class ProductItem:
    # OCR result
    name: str
    # If success to parse item name
    valid: bool
    # Button to click for the current item
    button: Button
    # All buttons on this page to click
    item_buttons: ButtonGrid

    def __init__(self, image, y, get_button=True):
        """
        Args:
            image:
            y (int):
            get_button (bool): if parse other items in the current page
        """
        self.image = image
        self.y = y
        self.valid = True
        self.name = None
        self.button = None
        self.items = []
        self.parse_item(get_button=get_button)

    def parse_item(self, get_button):
        if len(self.y) < 2:
            self.valid = False
            return

        y1, y2 = self.y

        # name
        if get_button:
            self.ocr_name(y1, y2)

        # button
        x1, x2 = ISLAND_PRODUCT_ITEMS.area[0] + 20, ISLAND_PRODUCT_ITEMS.area[2] - 20
        area = (x1, y1, x2, y2)
        self.button = Button(area=area, color=(), button=area, name='ISLAND_ITEM')
        if get_button:
            delta = 149
            up, down = self.grid_num(delta, y1, y2)
            shape_y = up + down + 1
            origin_y = y1 - up * delta
            self.item_buttons = ButtonGrid(origin=(x1, origin_y), delta=(0, delta),
                                           button_shape=(x2 - x1, y2 - y1),
                                           grid_shape=(1, shape_y), name='ITEMS')
            self.items = [ProductItem(self.image, (item.area[1], item.area[3]), get_button=False)
                          for item in self.item_buttons.buttons]
        else:
            self.ocr_name(y1, y2)


    @staticmethod
    def grid_num(delta, y1, y2):
        """
        Args:
            delta (int): grid delta
            y1 (int):
            y2 (int):

        Returns:
            tuple(int, int): grids above and below current grid
        """
        up = 0
        down = 0
        while y1 - delta > ISLAND_PRODUCT_ITEMS.area[1]:
            up += 1
            y1 -= delta
        while y2 + delta < ISLAND_PRODUCT_ITEMS.area[3]:
            down += 1
            y2 += delta
        return up, down

    def ocr_name(self, y1, y2):
        """
        Args:
            y1 (int):
            y2 (int):
        """
        area = (300, y1 + 14, 440, y2 - 84)
        button = Button(area=area, color=(), button=area, name='ITEM_NAME')
        ocr = ItemNameOcr(button, lang='cnocr', letter=(70, 70, 70))
        self.name = ocr.ocr(self.image)
        if not self.name or self.name not in deep_values(items_data_cn, depth=2):
            self.valid = False

    def __eq__(self, other):
        """
        Args:
            other (ProductItem):

        Returns:
            bool:
        """
        if not isinstance(other, ProductItem):
            return False
        if not self.valid or not other.valid:
            return False
        if self.name != other.name:
            return False

        return True


class IslandProjectRun(IslandUI):
    project = SelectedGrids([])
    total = SelectedGrids([])
    character: str

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
                                  for button in TEMPLATE_PROJECT.match_multi(image_gray)])
        return projects.select(valid=True)

    def project_receive(self, button, skip_first_screenshot=True):
        """
        Receive a project and enter role select page.

        Args:
            button (Button): project button to click

        Returns:
            bool: if success
        """
        self.device.click_record_clear()
        self.interval_clear([ISLAND_MANAGEMENT_CHECK, PROJECT_COMPLETE,
                             GET_ITEMS_ISLAND, ROLE_SELECT_ENTER])
        success = False
        enter = True
        click_timer = Timer(5, count=10).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.island_in_management(interval=5):
                self.device.click(button)
                click_timer.reset()
                continue

            if self.appear_then_click(ISLAND_MANAGEMENT, offset=(20, 20), interval=2):
                click_timer.reset()
                continue

            if self.handle_info_bar():
                click_timer.reset()
                continue

            if enter and self.appear_then_click(ROLE_SELECT_ENTER, offset=(5, 5), interval=2):
                success = True
                self.interval_clear(GET_ITEMS_ISLAND)
                click_timer.reset()
                continue

            if self.appear_then_click(PROJECT_COMPLETE, offset=(20, 20), interval=1):
                success = True
                enter = False
                self.interval_clear(GET_ITEMS_ISLAND)
                self.interval_reset(ROLE_SELECT_ENTER)
                click_timer.reset()
                continue

            if self.handle_get_items():
                enter = True
                self.interval_clear(ROLE_SELECT_ENTER)
                click_timer.reset()
                continue

            # handle island level up
            if not enter and click_timer.reached():
                self.device.click(GET_ITEMS_ISLAND)
                self.device.sleep(0.3)
                click_timer.reset()
                continue

            if self.appear(ROLE_SELECT_CONFIRM, offset=(20, 20)):
                break

            if not success:
                product = IslandProduct(self.device.image)
                if product.valid:
                    self.total = self.total.add_by_eq(SelectedGrids([product]))
                    self.device.click(ISLAND_CLICK_SAFE_AREA)
                    break
                else:
                    self.interval_clear(ROLE_SELECT_ENTER)

        return success

    def _project_character_select(self, click_button, check_button):
        """
        Select a specific character for an island project.

        Args:
            click_button (Button): character button to click
            check_button (Button):
        """
        skip_first_screenshot=True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.appear(check_button, offset=(20, 20)):
                break
            if self.appear(ROLE_SELECT_CONFIRM, offset=(20, 20), interval=2):
                self.device.click(click_button)
                continue

        self.interval_clear(ROLE_SELECT_CONFIRM)
        skip_first_screenshot=True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            if self.appear(ISLAND_AMOUNT_MAX, offset=(20, 20)):
                return True
            # game bug that page returns to ISLAND_MANAGEMENT_CHECK after clicking ROLE_SELECT_CONFIRM
            if self.island_in_management():
                return False

            if self.appear_then_click(ROLE_SELECT_CONFIRM, offset=(20, 20), interval=2):
                self.interval_clear(ISLAND_MANAGEMENT_CHECK)
                continue

    def project_character_select(self, character='manjuu', skip_first_screenshot=True):
        """
        Select a role to produce.

        Args:
            character (str): character name to select
            skip_first_screenshot (bool):

        Returns:
            bool: if selected
        """
        logger.info('Island select role')
        timeout = Timer(1.5, count=3).start()
        count = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                self.ui_ensure_management_page()
                return False

            image = self.image_crop((0, 0, 910, 1280), copy=False)
            sim, click_button = self.get_character_template(character).match_result(image)
            if sim > 0.9:
                check_button = self.get_character_check_button(character)
                return self._project_character_select(click_button, check_button)
            else:
                name = ' '.join(map(lambda x: x.capitalize(), character.split('_')))
                logger.info(f'No character {name} found')
                if count >= 2:
                    character = 'manjuu'
                count += 1
                continue

    @staticmethod
    def get_character_template(character):
        return globals().get(f'TEMPLATE_{character.upper()}', TEMPLATE_MANJUU)

    @staticmethod
    def get_character_check_button(character):
        return globals().get(f'PROJECT_{character.upper()}_CHECK', PRODUCT_MANJUU_CHECK)

    def get_current_product(self):
        """
        Get currently selected product on self.device.image.

        Returns:
            ProductItem: currently selected item
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
        return ProductItem(self.device.image, peaks)

    def product_select(self, option, trial=2, skip_first_screenshot=True):
        """
        Select a product in items list.

        Args:
            option (str): option to select
            trail (int): retry times
            skip_first_screenshot (bool):

        Returns:
            bool: if selected
        """
        logger.hr('Island Select Product')
        last = None
        retry = trial
        click_interval = Timer(1)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            current = self.get_current_product()
            if trial > 0 and not len(current.items):
                trial -= 1
                continue
            if trial <= 0:
                self.ui_ensure_management_page()
                return False

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
                if retry > 0:
                    retry -= 1
                    continue
                logger.info(f'Reach the bottom of items, did not match item {option}')
                self.ui_ensure_management_page()
                return False

            if drag:
                last = current.items[-1]
                self.device.click(last.button)
                self.island_drag_next_page((0, -300), ISLAND_PRODUCT_ITEMS.area, 0.5)

    def product_select_confirm(self, skip_first_screenshot=True):
        """
        Start the product after product selected.

        Args:
            skip_first_screenshot (bool):

        Returns:
            bool: if success
        """
        logger.info('Island product confirm')
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
                if self.image_color_count(PROJECT_START, color=(151, 155, 155), threshold=221, count=200):
                    if self.appear(PRODUCT_MANJUU_CHECK, offset=(20, 20)):
                        self.ui_ensure_management_page()
                        return True
                    else:
                        logger.warning('Product requirement is not satisfied, quitting and retrying')
                        self.ui_ensure_management_page()
                        return False

                if self.appear_then_click(ISLAND_AMOUNT_MAX, offset=(5, 5), interval=2):
                    timeout.reset()
                    continue

                button = PROJECT_START
                self.appear(button, offset=(100, 0))
                offset = tuple(np.subtract(button.button, button._button)[:2])
                product = IslandProduct(self.device.image, new=True, offset=offset)
                if product == last:
                    success = True
                    self.total = self.total.add_by_eq(SelectedGrids([product]))
                    timeout.reset()
                    continue
                last = product
            else:
                if self.appear_then_click(PROJECT_START, offset=(100, 0), interval=2):
                    timeout.reset()
                    self.interval_clear(ISLAND_MANAGEMENT_CHECK)
                    continue

                if self.info_bar_count():
                    self.ui_ensure_management_page()
                    return True
                if self.island_in_management():
                    return True

    def island_drag_next_page(self, vector, box, sleep=0.5):
        """
        Drag to the next page.

        Args:
            vector (tuple):
            box (tuple):
            sleep (float):
        """
        logger.info('Island drag to next page')
        p1, p2 = random_rectangle_vector(vector, box=box, random_range=(0, -5, 0, 5))
        self.device.drag(p1, p2, segments=2, shake=(0, 25), point_random=(0, 0, 0, 0), shake_random=(0, -5, 0, 5))
        self.device.sleep(sleep)

    def ensure_project(self, project, trial=7, skip_first_screenshot=True):
        """
        Ensure the specific project is in the current page.

        Args:
            project (IslandProject): the project to ensure
            trial (int): retry times
            skip_first_screenshot (bool):
        """
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
                logger.info(f'Ensured project: {project}')
                break

            self.island_drag_next_page((0, -500), ISLAND_PROJECT_SWIPE.area, 0.6)

    def project_receive_and_start(self, proj, button, character, option, ensure=True):
        """
        Receive and start a project is in the current page.

        Args:
            proj (IslandProject): the project to ensure
            button (Button): project button to click
            character (str): character to select
            option (str): option to select
            ensure (bool): whether to call ensure_project() after project start
        """
        if not self.project_receive(button):
            return True
        if not self.project_character_select(character):
            logger.warning('Island select role failed due to game bug, retrying')
            return False
        if not self.product_select(option):
            return True
        if not self.product_select_confirm():
            self.character = 'manjuu'
            self.ensure_project(proj)
            return False
        self.ui_ensure_management_page()
        if ensure:
            self.ensure_project(proj)
        return True

    def island_project_character(self, project: IslandProject):
        """
        Args:
            project (IslandProject):
        
        Returns:
            list[str]: a list of options of characters
        """
        proj_id = project.id
        return [self.config.__getattribute__(f'Island{proj_id}_Character{proj_slot}')
                for proj_slot in range(1, project.slot + 1)]

    def island_project_option(self, project: IslandProject):
        """
        Args:
            project (IslandProject):
        
        Returns:
            list[str]: a list of options of production items
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

    def island_project_run(self, names, trial=2, skip_first_screenshot=True):
        """
        Execute island run to receive and start project.

        Args:
            names (list[str]): a list of name for island receive
            trial (int): retry times
            skip_first_screenshot (bool):

        Returns:
            list[timedelta]: future finish timedelta
        """
        logger.hr('Island Project Run', level=1)
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
                logger.hr('Island Project')
                logger.attr('Project_name', proj)
                if proj.name == names[-1]:
                    end = True
                
                character_config = self.island_project_character(proj)
                option_config = self.island_project_option(proj)
                option_num = len(option_config)
                for button, character, option, index in zip(
                        proj.slot_buttons.buttons, character_config, option_config, range(option_num)):
                    if option is None:
                        continue
                    self.character = character
                    # retry 3 times because of a game bug
                    for _ in range(3):
                        ensure = not end or index != option_num - 1
                        if self.project_receive_and_start(proj, button, self.character, option, ensure):
                            break
                timeout.reset()

            if end:
                break
            self.island_drag_next_page((0, -500), ISLAND_PROJECT_SWIPE.area, 0.6)

        # task delay
        future_finish = sorted([f for f in self.total.get('finish_time') if f is not None])
        logger.info(f'Project finish: {[str(f) for f in future_finish]}')
        if not len(future_finish):
            logger.info('No island project running')
        return future_finish
