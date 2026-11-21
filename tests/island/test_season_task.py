"""Season-task recognition goldens and target-update behavior."""
from module.testing.screenshot import image

from module.island.season_task import IslandSeasonTask, NAME_AREA
from module.island.assets import ISLAND_SEASON_TASK_RECEIVE_ALL, TEMPLATE_ISLAND_SEASON_TASK_OBTAINED


class TestTasksJP:
    @image('island/season_task/dbc8f39c', server='jp')
    def test_six_pending_tasks_with_lower_grid_origin(self, main: IslandSeasonTask):
        # Read one frame directly; task IDs additionally depend on the live season clock.
        grid = main.get_season_task_grid()
        names = main.task_name_ocr.ocr(
            [main.image_crop(button) for button in grid.crop(NAME_AREA).buttons], direct_ocr=True)
        tasks = [dict(area=button.area, name=name,
                       obtained=TEMPLATE_ISLAND_SEASON_TASK_OBTAINED.match(main.image_crop(button)))
                  for button, name in zip(grid.buttons, names)]
        regions = [(entry['area'], 'task #{} obtained={}'.format(index, entry['obtained']))
                   for index, entry in enumerate(tasks)]
        available = main.appear(ISLAND_SEASON_TASK_RECEIVE_ALL, offset=(20, 20))
        receive_all_area = ISLAND_SEASON_TASK_RECEIVE_ALL.button if available else None
        actual = dict(tasks=tasks, receive_all=dict(available=available, area=receive_all_area))
        regions.append((receive_all_area or ISLAND_SEASON_TASK_RECEIVE_ALL.area,
                        'receive_all available={}'.format(available)))
        main.device.review(actual, regions)
        assert actual == {
            'receive_all': {'area': (1059, 618, 1093, 646), 'available': True},
            'tasks': [
                {'area': (42, 195, 418, 406), 'name': '落ち着いたお茶', 'obtained': False},
                {'area': (437, 195, 813, 406), 'name': '初めての接収', 'obtained': False},
                {'area': (832, 195, 1208, 406), 'name': '安心納品', 'obtained': False},
                {'area': (42, 425, 418, 636), 'name': '定期補充', 'obtained': False},
                {'area': (437, 425, 813, 636), 'name': '高効率納品', 'obtained': False},
                {'area': (832, 425, 1208, 636), 'name': '繊維補給', 'obtained': False},
            ],
        }

    @image('island/season_task/00d38aa2', server='jp')
    def test_six_pending_tasks_with_upper_grid_origin(self, main: IslandSeasonTask):
        # Read one frame directly; task IDs additionally depend on the live season clock.
        grid = main.get_season_task_grid()
        names = main.task_name_ocr.ocr(
            [main.image_crop(button) for button in grid.crop(NAME_AREA).buttons], direct_ocr=True)
        tasks = [dict(area=button.area, name=name,
                       obtained=TEMPLATE_ISLAND_SEASON_TASK_OBTAINED.match(main.image_crop(button)))
                  for button, name in zip(grid.buttons, names)]
        regions = [(entry['area'], 'task #{} obtained={}'.format(index, entry['obtained']))
                   for index, entry in enumerate(tasks)]
        available = main.appear(ISLAND_SEASON_TASK_RECEIVE_ALL, offset=(20, 20))
        receive_all_area = ISLAND_SEASON_TASK_RECEIVE_ALL.button if available else None
        actual = dict(tasks=tasks, receive_all=dict(available=available, area=receive_all_area))
        regions.append((receive_all_area or ISLAND_SEASON_TASK_RECEIVE_ALL.area,
                        'receive_all available={}'.format(available)))
        main.device.review(actual, regions)
        assert actual == {
            'receive_all': {'area': (1059, 618, 1093, 646), 'available': True},
            'tasks': [
                {'area': (42, 157, 418, 368), 'name': '安心依頼', 'obtained': False},
                {'area': (437, 157, 813, 368), 'name': '堅実なサポート', 'obtained': False},
                {'area': (832, 157, 1208, 368), 'name': '依頼のフロ', 'obtained': False},
                {'area': (42, 387, 418, 598), 'name': '発展の柱', 'obtained': False},
                {'area': (437, 387, 813, 598), 'name': '発展の中心', 'obtained': False},
                {'area': (832, 387, 1208, 598), 'name': '繁栄の礎', 'obtained': False},
            ],
        }


class TestTasksCN:
    @image('island/season_task/6da95f79', server='cn')
    def test_six_completed_tasks(self, main: IslandSeasonTask):
        # Read one frame directly; task IDs additionally depend on the live season clock.
        grid = main.get_season_task_grid()
        names = main.task_name_ocr.ocr(
            [main.image_crop(button) for button in grid.crop(NAME_AREA).buttons], direct_ocr=True)
        tasks = [dict(area=button.area, name=name,
                       obtained=TEMPLATE_ISLAND_SEASON_TASK_OBTAINED.match(main.image_crop(button)))
                  for button, name in zip(grid.buttons, names)]
        regions = [(entry['area'], 'task #{} obtained={}'.format(index, entry['obtained']))
                   for index, entry in enumerate(tasks)]
        available = main.appear(ISLAND_SEASON_TASK_RECEIVE_ALL, offset=(20, 20))
        receive_all_area = ISLAND_SEASON_TASK_RECEIVE_ALL.button if available else None
        actual = dict(tasks=tasks, receive_all=dict(available=available, area=receive_all_area))
        regions.append((receive_all_area or ISLAND_SEASON_TASK_RECEIVE_ALL.area,
                        'receive_all available={}'.format(available)))
        main.device.review(actual, regions)
        assert actual == {
            'receive_all': {'area': None, 'available': False},
            'tasks': [
                {'area': (42, 165, 418, 376), 'name': '田野坚盾', 'obtained': True},
                {'area': (437, 165, 813, 376), 'name': '工业血脉', 'obtained': True},
                {'area': (832, 165, 1208, 376), 'name': '香甜活力', 'obtained': True},
                {'area': (42, 395, 418, 606), 'name': '纤维补给', 'obtained': True},
                {'area': (437, 395, 813, 606), 'name': '芳香疗愈', 'obtained': True},
                {'area': (832, 395, 1208, 606), 'name': '便携快餐', 'obtained': True},
            ],
        }


class TestTasksEN:
    @image('island/season_task/f17ea41e', server='en')
    def test_three_completed_tasks(self, main: IslandSeasonTask):
        # Read one frame directly; task IDs additionally depend on the live season clock.
        grid = main.get_season_task_grid()
        names = main.task_name_ocr.ocr(
            [main.image_crop(button) for button in grid.crop(NAME_AREA).buttons], direct_ocr=True)
        tasks = [dict(area=button.area, name=name,
                       obtained=TEMPLATE_ISLAND_SEASON_TASK_OBTAINED.match(main.image_crop(button)))
                  for button, name in zip(grid.buttons, names)]
        regions = [(entry['area'], 'task #{} obtained={}'.format(index, entry['obtained']))
                   for index, entry in enumerate(tasks)]
        available = main.appear(ISLAND_SEASON_TASK_RECEIVE_ALL, offset=(20, 20))
        receive_all_area = ISLAND_SEASON_TASK_RECEIVE_ALL.button if available else None
        actual = dict(tasks=tasks, receive_all=dict(available=available, area=receive_all_area))
        regions.append((receive_all_area or ISLAND_SEASON_TASK_RECEIVE_ALL.area,
                        'receive_all available={}'.format(available)))
        main.device.review(actual, regions)
        assert actual == {
            'receive_all': {'area': None, 'available': False},
            'tasks': [
                {'area': (42, 376, 418, 587), 'name': 'watching the Fields', 'obtained': True},
                {'area': (437, 376, 813, 587), 'name': 'The Beasts Hunger', 'obtained': True},
                {'area': (832, 376, 1208, 587), 'name': 'More Rice!', 'obtained': True},
            ],
        }


class TaskTargetConfig:
    def __init__(self, target):
        self.target = target
        self.set_calls = []
        self.delayed = False

    def cross_get(self, _key, _default=None):
        return self.target

    def cross_set(self, key, value):
        self.set_calls.append((key, value))

    def task_delay(self, **_kwargs):
        self.delayed = True


class TestTargetUpdates:
    def test_unchanged_season_target_does_not_replan_after_date_change(self):
        task = object.__new__(IslandSeasonTask)
        task.config = TaskTargetConfig('2603: 250')
        task.device = object()
        task.ui_ensure = lambda _page: None
        task.island_season_bottom_navbar_ensure = lambda **_kwargs: None
        task.receive_all_reward = lambda: None
        task.scan_all = lambda: [80001407]

        task.run()

        assert task.config.set_calls == []
        assert task.config.delayed
