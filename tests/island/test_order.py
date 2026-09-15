from datetime import datetime

import module.config.server as server
from module.island.data import DIC_ISLAND_ACTIVITY
from module.island.order import IslandOrder, get_season_order_id


class FakeConfig:
    def __init__(self, stuck_order_id):
        self.stuck_order_id = stuck_order_id
        self.delayed = False

    def cross_get(self, _key, _default=None):
        return self.stuck_order_id

    def task_delay(self, **_kwargs):
        self.delayed = True


def test_repeated_autumn_order_prefers_current_activity():
    activity = DIC_ISLAND_ACTIVITY[990023]
    start = datetime.strptime(activity['start_time'][server.server], '%Y-%m-%d %H:%M:%S')
    end = datetime.strptime(activity['end_time'][server.server], '%Y-%m-%d %H:%M:%S')
    assert get_season_order_id(
        {4011: 5, 4013: 5},
        current_time=start + (end - start) / 2,
    ) == 100060


def test_unchanged_stuck_order_does_not_replan_after_date_change():
    order = object.__new__(IslandOrder)
    order.config = FakeConfig(100046)
    order.device = object()
    order.ui_ensure = lambda _page: None
    order.loop = lambda: iter([None])
    order.detect_all_orders = lambda: None
    order.run_any_order = lambda: False
    order.season_orders = [object()]
    order.regular_cooldown_orders = []

    order.run()

    assert order.config.delayed
