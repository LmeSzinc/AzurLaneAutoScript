from module.island.season_task import IslandSeasonTask


class FakeConfig:
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


def test_unchanged_season_target_does_not_replan_after_date_change():
    task = object.__new__(IslandSeasonTask)
    task.config = FakeConfig('2603: 250')
    task.device = object()
    task.ui_ensure = lambda _page: None
    task.island_season_bottom_navbar_ensure = lambda **_kwargs: None
    task.receive_all_reward = lambda: None
    task.scan_all = lambda: [80001407]

    task.run()

    assert task.config.set_calls == []
    assert task.config.delayed
