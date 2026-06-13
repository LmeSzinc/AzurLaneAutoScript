from jellyfish import levenshtein_distance

from module.base.timer import Timer
from module.combat.assets import GET_ITEMS_1
import module.config.server as server
from module.base.button import ButtonGrid
from module.base.decorator import cached_property, del_cached_property
from module.island.assets import *
from module.island.data import DIC_ISLAND_TASK
from module.island.ui import IslandUI
from module.island.utils import item_mapping_to_yaml, load_item_mapping, normalize_item_keys
from module.logger import logger
from module.map_detection.utils import Points
from module.ocr.ocr import Ocr
from module.ui.navbar import Navbar
from module.ui.page import page_island_season
from module.ui.scroll import Scroll


DETECT_AREA = (42, 171, 1206, 604)
ICON_AREA = (21, 133, 225, 195)
TAB_DELTA = (395, 230)
TAB_SIZE = (376, 211)
NAME_AREA = (29, 18, 200, 48)
ISLAND_SEASON_TASK_SCROLL = Scroll(
    ISLAND_SEASON_TASK_SCROLL_AREA.button,
    color=(128, 128, 128),
    name="ISLAND_SEASON_TASK_SCROLL"
)

class IslandSeasonTask(IslandUI):
    @cached_property
    def _island_season_bottom_navbar(self):
        """
        6 options:
            homepage,
            pt_reward,
            season_task,
            season_shop,
            season_rank,
            season_history
        """
        island_season_bottom_navbar = ButtonGrid(
            origin=(14, 677), delta=(213, 0),
            button_shape=(186, 33), grid_shape=(6, 1),
            name='ISLAND_SEASON_BOTTOM_NAVBAR'
        )
        return Navbar(grids=island_season_bottom_navbar,
                      active_color=(237, 237, 237),
                      inactive_color=(65, 78, 96),
                      active_count=500,
                      inactive_count=500)

    def island_season_bottom_navbar_ensure(self, left=None, right=None):
        """
        Args:
            left (int):
                1 for homepage,
                2 for pt_reward,
                3 for season_task,
                4 for season_shop,
                5 for season_rank,
                6 for season_history
            right (int):
                1 for season_history,
                2 for season_rank,
                3 for season_shop,
                4 for season_task,
                5 for pt_reward,
                6 for homepage

        """
        if self._island_season_bottom_navbar.set(self, left=left, right=right):
            return True
        return False

    def _get_icons(self):
        area = (DETECT_AREA[0] + ICON_AREA[0], DETECT_AREA[1] + ICON_AREA[1] - NAME_AREA[1], DETECT_AREA[2], DETECT_AREA[3])
        image = self.image_crop(area, copy=True)
        icons = TEMPLATE_ISLAND_SEASON_REWARD.match_multi(image, similarity=0.7, threshold=5)
        icons = Points([(0., icon.area[1]) for icon in icons]).group(threshold=5)
        logger.attr('icons_count', len(icons))
        return icons

    @cached_property
    def season_task_grid(self):
        for _ in self.loop(timeout=3):
            grid = self.get_season_task_grid()
            if len(grid.buttons) >= 3:
                return grid
        return grid

    def get_season_task_grid(self):
        rows = self._get_icons()
        count = len(rows)
        if count >= 2:
            y_list = rows[:, 1]
            y1, y2 = y_list[0], y_list[-1]
            origin_y = min(y1, y2) + DETECT_AREA[1] - NAME_AREA[1]
            delta_y = TAB_DELTA[1]
        elif count < 1:
            logger.warning('No icons detected, assume at top')
            origin_y = DETECT_AREA[1] - NAME_AREA[1]
            delta_y = TAB_DELTA[1]
        else:
            origin_y = rows[0][1] + DETECT_AREA[1] - NAME_AREA[1]
            delta_y = TAB_DELTA[1]

        season_task_grid = ButtonGrid(
            origin=(DETECT_AREA[0], origin_y),
            delta=(TAB_DELTA[0], delta_y),
            button_shape=TAB_SIZE,
            grid_shape=(3, count), name='SEASON_TASK_GRID'
        )
        return season_task_grid

    @cached_property
    def task_names(self):
        return self.get_task_codename()

    @property
    def task_name_ocr(self):
        if server.server == 'jp':
            lang = 'jp'
        elif server.server == 'en':
            lang = 'azur_lane'
        else:
            lang = 'cnocr'
        ocr = Ocr([], lang=lang, letter=(57, 58, 60), name='task_name_ocr')
        return ocr

    def get_task_codename(self):
        name_grid = self.season_task_grid.crop(NAME_AREA, name='TASK_NAME_GRID')
        name_images = [self.image_crop(button.area, copy=True) for button in name_grid.buttons]
        names = self.task_name_ocr.ocr(name_images, direct_ocr=True)
        codenames = [self.task_name_to_codename(name) for name in names]
        logger.attr('Codenames', codenames)
        return codenames

    def task_name_to_codename(self, name):
        min_distance = float('inf')
        code = None
        corrected_name = None
        for key, item in DIC_ISLAND_TASK.items():
            distance = levenshtein_distance(name, item['name'][server.server])
            if distance < min_distance:
                min_distance = distance
                code = key
                corrected_name = item['name'][server.server]
        if name != corrected_name:
            logger.warning(f'Task name corrected: {name} -> {corrected_name}')
        return code

    def handle_island_get_items(self):
        if self.appear(GET_ITEMS_1, offset=(20, 100), interval=3):
            self.device.click(ISLAND_SEASON_TASK_RECEIVE_ALL)
            return True
        if self.has_white_band():
            if self.appear(page_island_season.check_button):
                return False
            self.device.click(ISLAND_SEASON_TASK_RECEIVE_ALL)
            return True
        return False

    def receive_all_reward(self):
        clicked = False
        confirm_timer = Timer(3, count=6)
        for _ in self.loop(skip_first=False):
            if self.appear_then_click(ISLAND_SEASON_TASK_RECEIVE_ALL, interval=2, offset=(20, 20)):
                clicked = True
                confirm_timer.reset()
                continue
            if self.handle_island_additional():
                confirm_timer.reset()
                continue
            if confirm_timer.reached():
                if clicked:
                    logger.info('Receive all rewards confirmed')
                else:
                    logger.info('No rewards to receive')
                break

    def scan_all(self):
        ISLAND_SEASON_TASK_SCROLL.set_top(main=self, skip_first_screenshot=False)
        logger.hr('scanning season tasks')
        unfinished_tasks = []
        early_stop = False
        while 1:
            for task_id, button in zip(self.task_names, self.season_task_grid.buttons):
                image = self.image_crop(button.area, copy=True)
                if TEMPLATE_ISLAND_SEASON_TASK_OBTAINED.match(image):
                    early_stop = True
                    break
                else:
                    unfinished_tasks.append(task_id)
            if early_stop:
                logger.info(f'Detect obtained task, early stop scanning')
                break
            if ISLAND_SEASON_TASK_SCROLL.at_bottom(main=self):
                break
            else:
                ISLAND_SEASON_TASK_SCROLL.next_page(main=self, skip_first_screenshot=False)
                del_cached_property(self, 'season_task_grid')
                del_cached_property(self, 'task_names')
                continue
        logger.info(f'Unfinished tasks: {unfinished_tasks}')
        return unfinished_tasks

    def run(self):
        self.ui_ensure(page_island_season)
        self.island_season_bottom_navbar_ensure(left=3)
        self.receive_all_reward()
        yaml_text = self.config.cross_get("IslandSeasonTask.IslandSeasonTask.TaskTarget", "{}")
        old_target = normalize_item_keys(load_item_mapping(yaml_text, config_name='TaskTarget'))
        new_target = {}
        unfinished_tasks = self.scan_all()
        for task_id in unfinished_tasks:
            target = DIC_ISLAND_TASK[task_id]['target']
            if target:
                item_id = list(target.keys())[0]
                new_target[item_id] = new_target.get(item_id, 0) + target[item_id]
        new_target = normalize_item_keys(new_target)
        if new_target != old_target:
            yaml_text = item_mapping_to_yaml(new_target, use_item_name=True)
            self.config.cross_set("IslandSeasonTask.IslandSeasonTask.TaskTarget", yaml_text)
            from module.island_handler.production_planner import IslandProductionPlanner
            IslandProductionPlanner(self.config, self.device).run()
        self.config.task_delay(server_update=True)
