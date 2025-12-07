import module.config.server as server
from module.base.button import ButtonGrid
from module.base.decorator import cached_property, del_cached_property, Config
from module.base.timer import Timer
from module.base.utils import area_offset
from module.island.assets import *
from module.island.data import DIC_ISLAND_SEASONAL_TASK
from module.island.ui import IslandUI, ISLAND_SEASON_TASK_SCROLL
from module.logger import logger
from module.map_detection.utils import Points
from module.ocr.ocr import DigitCounter, Ocr
from module.ui.page import page_island_season

if server.server == 'cn':
    lang = 'cnocr'
elif server.server == 'en':
    lang = 'azur_lane'
else:
    lang = server.server
TASK_NAME_OCR = Ocr([], lang=lang, letter=(64, 64, 64), name='TASK_NAME_OCR')
TASK_COUNTER_OCR = DigitCounter([], letter=(128, 128, 128), name='TASK_COUNTER_OCR')

class IslandSeasonTaskScanner(IslandUI):
    def _get_bars(self):
        """
        Returns:
            np.array: [[x1, y1], [x2, y2]], location of the bar icon upper left corner.
        """
        area = (43, 178, 875, 478)
        image = self.image_crop(area, copy=True)
        bars = TEMPLATE_ISLAND_SEASON_TASK_ICON.match_multi(image, threshold=5)
        bars = Points([(0., b.area[1]) for b in bars]).group(threshold=5)
        logger.attr('bars_icon', len(bars))
        return bars

    def wait_until_bar_appear(self, skip_first_screenshot=False):
        """
        After entering season task page,
        tasks are not loaded that fast,
        wait until any bar icon appears.
        """
        confirm_timer = Timer(1.5, count=3).start()
        for _ in self.loop(skip_first=skip_first_screenshot):
            bars = self._get_bars()
            if len(bars):
                if confirm_timer.reached():
                    return
                else:
                    pass
            else:
                confirm_timer.reset()

    @cached_property
    def task_grid(self):
        return self.task_bar_grid()

    def task_bar_grid(self):
        """
        Returns:
            ButtonGrid:
        """
        bars = self._get_bars()
        count = len(bars)
        if count == 0:
            logger.warning('Unable to find bar icon, assume task list is at top')
            origin_y = 178
            delta_y = 229
            row = 2
        elif count == 1:
            y_list = bars[:, 1]
            # -16 to adjust the bar position to grid position
            origin_y = y_list[0] - 16 + 178
            delta_y = 229
            row = 1
        elif count == 2:
            y_list = bars[:, 1]
            origin_y = min(y_list) - 16 + 178
            delta_y = abs(y_list[1] - y_list[0])
            row = 2
        else:
            logger.warning(f'Too many bars found ({count}), assume max rows')
            y_list = bars[:, 1]
            origin_y = min(y_list) - 16 + 178
            delta_y = abs(y_list[1] - y_list[0])
            row = 2
        task_grid = ButtonGrid(
            origin=(43, origin_y), delta=(394, delta_y),
            button_shape=(375, 210), grid_shape=(3, row),
            name='SEASONAL_TASK_GRID'
        )
        return task_grid

    @Config.when(SERVER='jp')
    def task_id_parse(self, string):
        string = string.replace('一', 'ー').replace('へ', 'ヘ')
        import jellyfish
        min_key = ''
        min_distance = 100
        for key, value in DIC_ISLAND_SEASONAL_TASK.items():
            distance = jellyfish.levenshtein_distance(value['name']['jp'], string)
            if distance < min_distance:
                min_distance = distance
                min_key = key
        if min_distance < 3:
            return min_key
        logger.warning(f'Unknown task name: {string}')
        return None

    @Config.when(SERVER=None)
    def task_id_parse(self, string):
        for key, value in DIC_ISLAND_SEASONAL_TASK.items():
            if string == value['name'][server.server]:
                return key
        logger.warning(f'Unknown task name: {string}')
        return None

    def predict(self, grid: ButtonGrid):
        """
        Predicts all tasks in the given grid.

        Args:
            grid (ButtonGrid):
        """
        name_area = (30, 18, 250, 52)
        counter_area = (270, 20, 360, 50)
        name_list = [self.image_crop(area, copy=True) for area in grid.crop(name_area).buttons]
        name_list = TASK_NAME_OCR.ocr(name_list, direct_ocr=True)
        task_id_list = [self.task_id_parse(name) for name in name_list]
        counter_list = [self.image_crop(area, copy=True) for area in grid.crop(counter_area).buttons]
        counter_list = [
            TASK_COUNTER_OCR.ocr([image], direct_ocr=True)
            for image in counter_list
        ]
        for task_id, counter_result, button in zip(task_id_list, counter_list, grid.buttons):
            if task_id is None:
                continue
            target = DIC_ISLAND_SEASONAL_TASK[task_id]['target']
            if target:
                target_item = list(target.keys())[0]
                current, _, total = counter_result
                obtained = TEMPLATE_ISLAND_SEASON_TASK_OBTAINED.match(self.image_crop(button, copy=True))
                yield task_id, (target_item, current, total), obtained

    def scan_all(self):
        """
        Scans all seasonal tasks on the island season page.

        Returns:
            dict: {
                recipe_id: (item_id, current, total)
            }
        """
        self.wait_until_bar_appear()
        logger.hr('Scanning seasonal tasks')
        ISLAND_SEASON_TASK_SCROLL.set_top(main=self)
        unfinished_tasks = {}
        while 1:
            for task_id, (target_item, current, total), obtained in self.predict(self.task_grid):
                if current < total:
                    unfinished_tasks[task_id] = (target_item, current, total)
                if obtained:
                    logger.info(f'Detect obtained task, early stop scanning')
                    return unfinished_tasks
            if ISLAND_SEASON_TASK_SCROLL.at_bottom(main=self):
                logger.info('Task list reach bottom, stop')
                break
            else:
                ISLAND_SEASON_TASK_SCROLL.next_page(main=self, page=0.5)
                del_cached_property(self, 'task_grid')
                continue
        return unfinished_tasks

    def run(self):
        """
        Pages:
            in: Any page
            out: page_island

        Returns:
            dict: {
                recipe_id: (item_id, current, total)
            }
        """
        self.ui_ensure(page_island_season)
        self.island_season_bottom_navbar_ensure(left=3)
        result = self.scan_all()
        return result
