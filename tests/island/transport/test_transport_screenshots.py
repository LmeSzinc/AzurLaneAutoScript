"""Transport slot, requirement and reward goldens from real JP and CN captures."""

from module.base.utils import crop
from module.island.assets import ISLAND_TRANSPORT_LIST_REFRESH, ISLAND_TRANSPORT_SUBMIT
from module.island.transport import (
    IslandTransport, REWARD_GRID, SLOT_COUNT, SUBMISSION_GRID, primary_badge_area, primary_counter_area,
)
from module.testing.screenshot import image


def slot_snapshot(main, view='content'):
    counters = main.transport_slot_counters()
    actual = {
        'counter_areas': [button.area for button in main.transport_slot_counter_grid.buttons],
        'counters': [(current, total) for current, _, total in counters],
        'requirements': {},
        'rewards': {},
        'states': main.transport_slot_states(),
        'submit_enabled': [main.slot_appear(ISLAND_TRANSPORT_SUBMIT, slot) for slot in range(SLOT_COUNT)],
    }
    regions = [(button.area, 'P{} {}/{} {}'.format(
        slot + 1, *actual['counters'][slot], actual['states'][slot]))
        for slot, button in enumerate(main.transport_slot_counter_grid.buttons)]
    for slot, state in enumerate(actual['states']):
        if state != 'ready':
            continue
        if view == 'content':
            cards = [(SUBMISSION_GRID[card, slot].area, primary_counter_area(card, slot), 'primary_submission')
                     for card in range(3)]
            items, stock, unknown = main.read_submissions(cards)
            actual['requirements'][slot] = {'items': items, 'stock': stock, 'unknown': unknown}
        else:
            cards = [(REWARD_GRID[card, slot].area, primary_badge_area(card, slot), 'primary_reward')
                     for card in range(3)]
            actual['rewards'][slot] = {
                'items': main.read_rewards(cards),
                'amounts': main.transport_badge_ocr.ocr(
                    [crop(main.device.image, badge) for _, badge, _ in cards], direct_ocr=True),
            }
        for card, (area, counter, _) in enumerate(cards):
            regions += [(area, 'P{} {} {}'.format(slot + 1, view, card + 1)),
                        (counter, 'P{} count {}'.format(slot + 1, card + 1))]
    main.device.review(actual, regions)
    return actual


class TestTransportSlotsCN:
    @image('island/transport/94a8ff0c', server='cn')
    def test_available_slots_include_disabled_submit(self, main: IslandTransport):
        assert slot_snapshot(main) == {
            'counter_areas': [
                (1074, 136, 1102, 158),
                (1074, 311, 1102, 333),
                (1074, 486, 1102, 508),
            ],
            'counters': [(1, 1), (1, 1), (1, 1)],
            'requirements': {
                0: {
                    'items': [(2603, 14), (2010, 26), (2009, 14)],
                    'stock': {2009: 173, 2010: 0, 2603: 250},
                    'unknown': False,
                },
                1: {
                    'items': [(2802, 8), (2010, 13), (2522, 2)],
                    'stock': {2010: 0, 2522: 15, 2802: 0},
                    'unknown': False,
                },
                2: {
                    'items': [(2701, 48)],
                    'stock': {2701: 0},
                    'unknown': False,
                },
            },
            'rewards': {},
            'states': ['ready', 'ready', 'ready'],
            'submit_enabled': [True, True, False],
        }

    @image('island/transport/9c969173', server='cn')
    def test_available_rewards_skip_completed_slot(self, main: IslandTransport):
        assert slot_snapshot(main, view='reward') == {
            'counter_areas': [
                (1074, 136, 1102, 158),
                (1074, 311, 1102, 333),
                (1074, 486, 1102, 508),
            ],
            'counters': [(0, 1), (1, 1), (1, 1)],
            'requirements': {},
            'rewards': {
                1: {
                    'items': {2009: 41, 2604: 19},
                    'amounts': [41, 19, 0],
                },
                2: {
                    'items': {2011: 17, 2604: 10, 2801: 23},
                    'amounts': [23, 10, 17],
                },
            },
            'states': ['completed', 'ready', 'ready'],
            'submit_enabled': [False, False, False],
        }


class TestTransportSlotsJP:
    @image('island/transport/d95ee44b', server='jp')
    def test_two_available_slots_and_third_running(self, main: IslandTransport):
        assert slot_snapshot(main) == {
            'counter_areas': [
                (1070, 136, 1099, 157),
                (1070, 311, 1099, 332),
                (1070, 486, 1099, 507),
            ],
            'counters': [(1, 1), (1, 1), (0, 1)],
            'requirements': {
                0: {
                    'items': [(2702, 10), (2802, 5)],
                    'stock': {2702: 151, 2802: 228},
                    'unknown': False,
                },
                1: {
                    'items': [(2017, 30), (2010, 26), (2018, 12)],
                    'stock': {2010: 185, 2017: 140, 2018: 273},
                    'unknown': False,
                },
            },
            'rewards': {},
            'states': ['ready', 'ready', 'running'],
            'submit_enabled': [True, True, False],
        }

    @image('island/transport/85ae45f7', server='jp')
    def test_first_running_and_two_available_slots(self, main: IslandTransport):
        assert slot_snapshot(main) == {
            'counter_areas': [
                (1070, 136, 1099, 157),
                (1070, 311, 1099, 332),
                (1070, 486, 1099, 507),
            ],
            'counters': [(0, 1), (1, 1), (1, 1)],
            'requirements': {
                1: {
                    'items': [(2600, 14), (2701, 9), (2011, 17)],
                    'stock': {2011: 103, 2600: 67, 2701: 206},
                    'unknown': False,
                },
                2: {
                    'items': [(2012, 21), (2801, 15), (2009, 14)],
                    'stock': {2009: 210, 2012: 112, 2801: 203},
                    'unknown': False,
                },
            },
            'rewards': {},
            'states': ['running', 'ready', 'ready'],
            'submit_enabled': [False, True, True],
        }

    @image('island/transport/1104c514', server='jp')
    def test_first_available_and_two_running_slots(self, main: IslandTransport):
        assert slot_snapshot(main) == {
            'counter_areas': [
                (1070, 136, 1099, 157),
                (1070, 311, 1099, 332),
                (1070, 486, 1099, 507),
            ],
            'counters': [(1, 1), (0, 1), (0, 1)],
            'requirements': {
                0: {
                    'items': [(5005, 16), (2522, 8)],
                    'stock': {2522: 2118, 5005: 179},
                    'unknown': False,
                },
            },
            'rewards': {},
            'states': ['ready', 'running', 'running'],
            'submit_enabled': [True, False, False],
        }

    @image('island/transport/03628f50', server='jp')
    def test_completed_slots_take_precedence_over_exhausted_counters(self, main: IslandTransport):
        assert slot_snapshot(main) == {
            'counter_areas': [
                (1070, 136, 1099, 157),
                (1070, 311, 1099, 332),
                (1070, 486, 1099, 507),
            ],
            'counters': [(0, 1), (0, 1), (0, 1)],
            'requirements': {},
            'rewards': {},
            'states': ['completed', 'completed', 'completed'],
            'submit_enabled': [False, False, False],
        }

    @image('island/transport/3fc147aa', server='jp')
    def test_empty_slots_without_remaining_trips(self, main: IslandTransport):
        assert main.transport_refresh_status() == ('unknown', None)
        main.device.review({'refresh_state': 'unknown'}, [
            (ISLAND_TRANSPORT_LIST_REFRESH.area, 'no list refresh control on primary view'),
        ])
        assert slot_snapshot(main) == {
            'counter_areas': [
                (1070, 136, 1099, 157),
                (1070, 311, 1099, 332),
                (1070, 486, 1099, 507),
            ],
            'counters': [(0, 1), (0, 1), (0, 1)],
            'requirements': {},
            'rewards': {},
            'states': ['empty', 'empty', 'empty'],
            'submit_enabled': [False, False, False],
        }

    @image('island/transport/2fa107f3', server='jp')
    def test_assigned_slot_without_remaining_trips(self, main: IslandTransport):
        assert slot_snapshot(main) == {
            'counter_areas': [
                (1070, 136, 1099, 157),
                (1070, 311, 1099, 332),
                (1070, 486, 1099, 507),
            ],
            'counters': [(0, 1), (0, 1), (0, 1)],
            'requirements': {},
            'rewards': {},
            'states': ['exhausted', 'empty', 'empty'],
            'submit_enabled': [False, False, False],
        }

    @image('island/transport/aa5471d7', server='jp')
    def test_available_slots_in_reward_view(self, main: IslandTransport):
        assert slot_snapshot(main, view='reward') == {
            'counter_areas': [
                (1070, 136, 1099, 157),
                (1070, 311, 1099, 332),
                (1070, 486, 1099, 507),
            ],
            'counters': [(1, 1), (1, 1), (1, 1)],
            'requirements': {},
            'rewards': {
                0: {
                    'items': {2603: 17, 2604: 25},
                    'amounts': [25, 17, 0],
                },
                1: {
                    'items': {2012: 10, 2016: 41, 2703: 10},
                    'amounts': [41, 10, 10],
                },
                2: {
                    'items': {2604: 20, 2702: 6, 5001: 22},
                    'amounts': [20, 6, 22],
                },
            },
            'states': ['ready', 'ready', 'ready'],
            'submit_enabled': [False, False, False],
        }

    @image('island/transport/3a15d383', server='jp')
    def test_rewards_for_two_available_slots(self, main: IslandTransport):
        assert slot_snapshot(main, view='reward') == {
            'counter_areas': [
                (1070, 136, 1099, 157),
                (1070, 311, 1099, 332),
                (1070, 486, 1099, 507),
            ],
            'counters': [(1, 1), (1, 1), (0, 1)],
            'requirements': {},
            'rewards': {
                0: {
                    'items': {2011: 44, 2019: 13},
                    'amounts': [44, 13, 0],
                },
                1: {
                    'items': {2007: 3, 2009: 31, 2021: 5},
                    'amounts': [31, 5, 3],
                },
            },
            'states': ['ready', 'ready', 'other'],
            'submit_enabled': [False, False, False],
        }

    @image('island/transport/18be9f23', server='jp')
    def test_requirements_with_overlapping_stock(self, main: IslandTransport):
        # Potato stock covers the preceding need's last digit, so the reader uses its upper bound, 19.
        assert slot_snapshot(main) == {
            'counter_areas': [
                (1070, 136, 1099, 157),
                (1070, 311, 1099, 332),
                (1070, 486, 1099, 507),
            ],
            'counters': [(1, 1), (1, 1), (1, 1)],
            'requirements': {
                0: {
                    'items': [(2521, 19), (2005, 29), (2603, 7)],
                    'stock': {2005: 119365, 2521: 329, 2603: 0},
                    'unknown': False,
                },
                1: {
                    'items': [(2007, 6), (2012, 36)],
                    'stock': {2007: 99, 2012: 158},
                    'unknown': False,
                },
                2: {
                    'items': [(2703, 8), (2010, 46)],
                    'stock': {2010: 185, 2703: 186},
                    'unknown': False,
                },
            },
            'rewards': {},
            'states': ['ready', 'ready', 'ready'],
            'submit_enabled': [True, True, True],
        }

    @image('island/transport/6442e913', server='jp')
    def test_rewards_with_three_available_slots(self, main: IslandTransport):
        assert slot_snapshot(main, view='reward') == {
            'counter_areas': [
                (1070, 136, 1099, 157),
                (1070, 311, 1099, 332),
                (1070, 486, 1099, 507),
            ],
            'counters': [(1, 1), (1, 1), (1, 1)],
            'requirements': {},
            'rewards': {
                0: {
                    'items': {2016: 37, 2600: 9, 2801: 7},
                    'amounts': [9, 37, 7],
                },
                1: {
                    'items': {2017: 29, 2602: 47, 5001: 46},
                    'amounts': [46, 29, 47],
                },
                2: {
                    'items': {2022: 12, 2522: 4},
                    'amounts': [12, 4, 0],
                },
            },
            'states': ['ready', 'ready', 'ready'],
            'submit_enabled': [False, False, False],
        }
