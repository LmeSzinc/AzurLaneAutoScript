"""Order recognition goldens and season-order scheduling rules."""
from datetime import datetime

import module.config.server as server
from module.island.data import DIC_ISLAND_ACTIVITY
from module.island.order import IslandOrder, get_season_order_id
from module.testing.screenshot import image


class TestRequirementsJP:
    @image('island/order/e2e401e9', server='jp')
    def test_regular_and_cooldown_orders(self, main: IslandOrder):
        main.detect_all_orders()
        orders = {
            kind: [dict(name=button.name, area=button.area, button=button.button)
                   for button in getattr(main, kind)]
            for kind in ('regular_orders', 'regular_cooldown_orders', 'urgent_orders', 'season_orders')
        }
        requirements = main.scan_current_order_requirements()
        actual = dict(orders=orders, requirements=requirements)
        regions = [(entry['area'], '{} #{}'.format(kind, index))
                   for kind, entries in orders.items() for index, entry in enumerate(entries)]
        regions += [(button.area, 'requirement #{}'.format(index))
                    for index, button in enumerate(main.requirement_grid.buttons)]
        main.device.review(actual, regions)
        assert actual == {
            'orders': {
                'regular_cooldown_orders': [
                    {
                        'area': (716, 497, 820, 601),
                        'button': (724, 505, 812, 593),
                        'name': 'ORDER_AT_768_549',
                    },
                    {
                        'area': (253, 255, 357, 359),
                        'button': (261, 263, 349, 351),
                        'name': 'ORDER_AT_305_307',
                    },
                ],
                'regular_orders': [
                    {
                        'area': (424, 66, 528, 170),
                        'button': (432, 74, 520, 162),
                        'name': 'ORDER_AT_476_118',
                    },
                    {
                        'area': (581, 401, 685, 505),
                        'button': (589, 409, 677, 497),
                        'name': 'ORDER_AT_633_453',
                    },
                ],
                'season_orders': [],
                'urgent_orders': [],
            },
            'requirements': {2602: (0, 22, -22), 2802: (130, 1, 129)},
        }

    @image('island/order/e601dbec', server='jp')
    def test_regular_and_urgent_orders(self, main: IslandOrder):
        main.detect_all_orders()
        orders = {
            kind: [dict(name=button.name, area=button.area, button=button.button)
                   for button in getattr(main, kind)]
            for kind in ('regular_orders', 'regular_cooldown_orders', 'urgent_orders', 'season_orders')
        }
        requirements = main.scan_current_order_requirements()
        actual = dict(orders=orders, requirements=requirements)
        regions = [(entry['area'], '{} #{}'.format(kind, index))
                   for kind, entries in orders.items() for index, entry in enumerate(entries)]
        regions += [(button.area, 'requirement #{}'.format(index))
                    for index, button in enumerate(main.requirement_grid.buttons)]
        main.device.review(actual, regions)
        assert actual == {
            'orders': {
                'regular_cooldown_orders': [],
                'regular_orders': [
                    {
                        'area': (715, 497, 819, 601),
                        'button': (723, 505, 811, 593),
                        'name': 'ORDER_AT_767_549',
                    },
                    {
                        'area': (649, 42, 753, 146),
                        'button': (657, 50, 745, 138),
                        'name': 'ORDER_AT_701_94',
                    },
                ],
                'season_orders': [],
                'urgent_orders': [
                    {
                        'area': (576, 544, 680, 648),
                        'button': (584, 552, 672, 640),
                        'name': 'ORDER_AT_628_596',
                    },
                ],
            },
            'requirements': {2701: (116, 4, 112), 2800: (3093, 3, 3090)},
        }

    @image('island/order/0b608c56', server='jp')
    def test_multiple_regular_and_cooldown_orders(self, main: IslandOrder):
        main.detect_all_orders()
        orders = {
            kind: [dict(name=button.name, area=button.area, button=button.button)
                   for button in getattr(main, kind)]
            for kind in ('regular_orders', 'regular_cooldown_orders', 'urgent_orders', 'season_orders')
        }
        requirements = main.scan_current_order_requirements()
        actual = dict(orders=orders, requirements=requirements)
        regions = [(entry['area'], '{} #{}'.format(kind, index))
                   for kind, entries in orders.items() for index, entry in enumerate(entries)]
        regions += [(button.area, 'requirement #{}'.format(index))
                    for index, button in enumerate(main.requirement_grid.buttons)]
        main.device.review(actual, regions)
        assert actual == {
            'orders': {
                'regular_cooldown_orders': [
                    {
                        'area': (424, 65, 528, 169),
                        'button': (432, 73, 520, 161),
                        'name': 'ORDER_AT_476_117',
                    },
                ],
                'regular_orders': [
                    {
                        'area': (472, 379, 576, 483),
                        'button': (480, 387, 568, 475),
                        'name': 'ORDER_AT_524_431',
                    },
                    {
                        'area': (257, 507, 361, 611),
                        'button': (265, 515, 353, 603),
                        'name': 'ORDER_AT_309_559',
                    },
                    {
                        'area': (345, 513, 449, 617),
                        'button': (353, 521, 441, 609),
                        'name': 'ORDER_AT_397_565',
                    },
                ],
                'season_orders': [],
                'urgent_orders': [],
            },
            'requirements': {2006: (2275, 2, 2273), 5006: (0, 7, -7)},
        }


class TestRequirementsCN:
    @image('island/order/7cef7c22', server='cn')
    def test_four_regular_orders(self, main: IslandOrder):
        main.detect_all_orders()
        orders = {
            kind: [dict(name=button.name, area=button.area, button=button.button)
                   for button in getattr(main, kind)]
            for kind in ('regular_orders', 'regular_cooldown_orders', 'urgent_orders', 'season_orders')
        }
        requirements = main.scan_current_order_requirements()
        actual = dict(orders=orders, requirements=requirements)
        regions = [(entry['area'], '{} #{}'.format(kind, index))
                   for kind, entries in orders.items() for index, entry in enumerate(entries)]
        regions += [(button.area, 'requirement #{}'.format(index))
                    for index, button in enumerate(main.requirement_grid.buttons)]
        main.device.review(actual, regions)
        assert actual == {
            'orders': {
                'regular_cooldown_orders': [],
                'regular_orders': [
                    {
                        'area': (580, 402, 684, 506),
                        'button': (588, 410, 676, 498),
                        'name': 'ORDER_AT_632_454',
                    },
                    {
                        'area': (471, 380, 575, 484),
                        'button': (479, 388, 567, 476),
                        'name': 'ORDER_AT_523_432',
                    },
                    {
                        'area': (423, 66, 527, 170),
                        'button': (431, 74, 519, 162),
                        'name': 'ORDER_AT_475_118',
                    },
                    {
                        'area': (359, 279, 463, 383),
                        'button': (367, 287, 455, 375),
                        'name': 'ORDER_AT_411_331',
                    },
                ],
                'season_orders': [],
                'urgent_orders': [],
            },
            'requirements': {2006: (1035, 30, 1005), 2008: (22177, 27, 22150), 2602: (1, 24, -23)},
        }

    @image('island/order/344c3c01', server='cn')
    def test_regular_and_urgent_orders(self, main: IslandOrder):
        main.detect_all_orders()
        orders = {
            kind: [dict(name=button.name, area=button.area, button=button.button)
                   for button in getattr(main, kind)]
            for kind in ('regular_orders', 'regular_cooldown_orders', 'urgent_orders', 'season_orders')
        }
        requirements = main.scan_current_order_requirements()
        actual = dict(orders=orders, requirements=requirements)
        regions = [(entry['area'], '{} #{}'.format(kind, index))
                   for kind, entries in orders.items() for index, entry in enumerate(entries)]
        regions += [(button.area, 'requirement #{}'.format(index))
                    for index, button in enumerate(main.requirement_grid.buttons)]
        main.device.review(actual, regions)
        assert actual == {
            'orders': {
                'regular_cooldown_orders': [],
                'regular_orders': [
                    {
                        'area': (141, 237, 245, 341),
                        'button': (149, 245, 237, 333),
                        'name': 'ORDER_AT_193_289',
                    },
                    {
                        'area': (190, 80, 294, 184),
                        'button': (198, 88, 286, 176),
                        'name': 'ORDER_AT_242_132',
                    },
                    {
                        'area': (256, 507, 360, 611),
                        'button': (264, 515, 352, 603),
                        'name': 'ORDER_AT_308_559',
                    },
                    {
                        'area': (471, 522, 575, 626),
                        'button': (479, 530, 567, 618),
                        'name': 'ORDER_AT_523_574',
                    },
                ],
                'season_orders': [],
                'urgent_orders': [
                    {
                        'area': (580, 402, 684, 506),
                        'button': (588, 410, 676, 498),
                        'name': 'ORDER_AT_632_454',
                    },
                ],
            },
            'requirements': {2602: (1, 16, -15), 2701: (289, 1, 288), 5001: (198, 9, 189)},
        }


class TestRequirementsEN:
    @image('island/order/87430d6d', server='en')
    def test_regular_and_season_orders(self, main: IslandOrder):
        main.detect_all_orders()
        orders = {
            kind: [dict(name=button.name, area=button.area, button=button.button)
                   for button in getattr(main, kind)]
            for kind in ('regular_orders', 'regular_cooldown_orders', 'urgent_orders', 'season_orders')
        }
        requirements = main.scan_current_order_requirements()
        actual = dict(orders=orders, requirements=requirements)
        regions = [(entry['area'], '{} #{}'.format(kind, index))
                   for kind, entries in orders.items() for index, entry in enumerate(entries)]
        regions += [(button.area, 'requirement #{}'.format(index))
                    for index, button in enumerate(main.requirement_grid.buttons)]
        main.device.review(actual, regions)
        assert actual == {
            'orders': {
                'regular_cooldown_orders': [],
                'regular_orders': [
                    {
                        'area': (695, 194, 799, 298),
                        'button': (703, 202, 791, 290),
                        'name': 'ORDER_AT_747_246',
                    },
                    {
                        'area': (753, 27, 857, 131),
                        'button': (761, 35, 849, 123),
                        'name': 'ORDER_AT_805_79',
                    },
                    {
                        'area': (537, 81, 641, 185),
                        'button': (545, 89, 633, 177),
                        'name': 'ORDER_AT_589_133',
                    },
                    {
                        'area': (141, 238, 245, 342),
                        'button': (149, 246, 237, 334),
                        'name': 'ORDER_AT_193_290',
                    },
                ],
                'season_orders': [
                    {
                        'area': (587, 251, 691, 355),
                        'button': (595, 259, 683, 347),
                        'name': 'ORDER_AT_639_303',
                    },
                ],
                'urgent_orders': [],
            },
            'requirements': {2005: (1726, 7, 1719), 3005: (0, 6, -6), 3011: (83, 1, 82)},
        }


class StoredOrderConfig:
    def __init__(self, stuck_order_id):
        self.stuck_order_id = stuck_order_id
        self.delayed = False

    def cross_get(self, _key, _default=None):
        return self.stuck_order_id

    def task_delay(self, **_kwargs):
        self.delayed = True


class TestSeasonOrderScheduling:
    def test_repeated_autumn_order_prefers_current_activity(self):
        activity = DIC_ISLAND_ACTIVITY[990023]
        start = datetime.strptime(activity['start_time'][server.server], '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime(activity['end_time'][server.server], '%Y-%m-%d %H:%M:%S')
        assert get_season_order_id(
            {4011: 5, 4013: 5},
            current_time=start + (end - start) / 2,
        ) == 100060

    def test_unchanged_stuck_order_does_not_replan_after_date_change(self):
        order = object.__new__(IslandOrder)
        order.config = StoredOrderConfig(100046)
        order.device = object()
        order.ui_ensure = lambda _page: None
        order.loop = lambda: iter([None])
        order.detect_all_orders = lambda: None
        order.run_any_order = lambda: False
        order.season_orders = [object()]
        order.regular_cooldown_orders = []

        order.run()

        assert order.config.delayed
