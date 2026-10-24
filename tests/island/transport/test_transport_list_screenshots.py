"""Transport commission-list readers exercised against real screenshots."""

from module.base.utils import crop
from module.island.assets import ISLAND_TRANSPORT_LIST_REFRESH
from module.island.transport import IslandTransport, remove_row_mask
from module.testing.screenshot import image


def list_snapshot(main, mode):
    rows = main.transport_list_rows()
    selected = [bool(main.transport_row_selected(row)) for row in rows]
    unselected = [row for row, is_selected in zip(rows, selected) if not is_selected]
    selected_rows = [row for row, is_selected in zip(rows, selected) if is_selected]

    if mode == 'requirements':
        readings = main.transport_list_read_page(unselected, rewards=False)
        readings.update({row.index: main.transport_list_read_selected(row, rewards=False)[row.index]
                         for row in selected_rows})
    else:
        readings = main.transport_list_read_page(unselected, rewards=True)
        readings.update({row.index: main.transport_list_read_selected(row, rewards=True)[row.index]
                         for row in selected_rows})

    actual = {
        'rows': [
            {
                'index': row.index,
                'area': tuple(map(int, row.area)),
                'select_area': tuple(map(int, row.select_area)),
                'selected': is_selected,
            }
            for row, is_selected in zip(rows, selected)
        ],
        'readings': {},
    }
    regions = []
    for row, is_selected in zip(rows, selected):
        regions.extend([
            (row.area, 'row {} selected={}'.format(row.index, is_selected)),
            (row.select_area, 'row {} select area'.format(row.index)),
        ])
        if mode == 'requirements':
            value = readings[row.index]
            actual['readings'][row.index] = {
                'items': value[0], 'stock': value[1], 'unknown': value[2],
            }
            for card in range(3):
                regions.extend([
                    (row.submission_area(card), 'row {} requirement {}'.format(row.index, card + 1)),
                    (row.counter_area(card), 'row {} requirement count {}'.format(row.index, card + 1)),
                ])
        else:
            reading_image = remove_row_mask(main.device.image, row) if is_selected else main.device.image
            cards = [(row.reward_area(card), row.badge_area(card), 'list_reward') for card in range(3)]
            amounts = main.transport_badge_ocr.ocr(
                [crop(reading_image, badge) for _, badge, _ in cards], direct_ocr=True
            )
            actual['readings'][row.index] = {'items': readings[row.index], 'amounts': amounts}
            for card in range(3):
                regions.extend([
                    (row.reward_area(card), 'row {} reward {}'.format(row.index, card + 1)),
                    (row.badge_area(card), 'row {} reward amount {}'.format(row.index, card + 1)),
                ])
    main.device.review(actual, regions)
    return actual


@image('island/transport/c15e9c16', server='jp')
def test_requirements_top_jp(main: IslandTransport):
    assert list_snapshot(main, 'requirements') == {
        'readings': {
            1: {
                'items': [(2007, 11), (2016, 38)],
                'stock': {2007: 84, 2016: 219},
                'unknown': False,
            },
            2: {
                'items': [(2019, 26)],
                'stock': {2019: 30},
                'unknown': False,
            },
            3: {
                'items': [(2802, 4), (2019, 18)],
                'stock': {2019: 30, 2802: 133},
                'unknown': False,
            },
            4: {
                'items': [(2019, 8), (2012, 36)],
                'stock': {2012: 204, 2019: 30},
                'unknown': False,
            },
        },
        'rows': [
            {
                'area': (400, 170, 900, 260),
                'index': 1,
                'select_area': (760, 180, 880, 250),
                'selected': True,
            },
            {
                'area': (400, 274, 900, 364),
                'index': 2,
                'select_area': (760, 284, 880, 354),
                'selected': False,
            },
            {
                'area': (400, 378, 900, 468),
                'index': 3,
                'select_area': (760, 388, 880, 458),
                'selected': False,
            },
            {
                'area': (400, 482, 900, 572),
                'index': 4,
                'select_area': (760, 492, 880, 562),
                'selected': False,
            },
        ],
    }


@image('island/transport/5270a231', server='jp')
def test_requirements_bottom_jp(main: IslandTransport):
    assert list_snapshot(main, 'requirements') == {
        'readings': {
            3: {
                'items': [(2802, 4), (2019, 18)],
                'stock': {2019: 30, 2802: 133},
                'unknown': False,
            },
            4: {
                'items': [(2019, 8), (2012, 36)],
                'stock': {2012: 204, 2019: 30},
                'unknown': False,
            },
            5: {
                'items': [(2019, 26)],
                'stock': {2019: 30},
                'unknown': False,
            },
            6: {
                'items': [(2600, 16), (2522, 4)],
                'stock': {2522: 518, 2600: 50},
                'unknown': False,
            },
        },
        'rows': [
            {
                'area': (400, 165, 900, 255),
                'index': 3,
                'select_area': (760, 175, 880, 245),
                'selected': False,
            },
            {
                'area': (400, 269, 900, 359),
                'index': 4,
                'select_area': (760, 279, 880, 349),
                'selected': False,
            },
            {
                'area': (400, 373, 900, 463),
                'index': 5,
                'select_area': (760, 383, 880, 453),
                'selected': False,
            },
            {
                'area': (400, 477, 900, 567),
                'index': 6,
                'select_area': (760, 487, 880, 557),
                'selected': False,
            },
        ],
    }


@image('island/transport/685b7b2c', server='jp')
def test_rewards_top_selected_jp(main: IslandTransport):
    assert list_snapshot(main, 'rewards') == {
        'readings': {
            1: {
                'amounts': [7, 24, 0],
                'items': {2604: 24, 2702: 7},
            },
            2: {
                'amounts': [29, 32, 0],
                'items': {2016: 29, 2701: 32},
            },
            3: {
                'amounts': [13, 42, 0],
                'items': {2601: 42, 2703: 13},
            },
            4: {
                'amounts': [9, 3, 0],
                'items': {2605: 3, 2702: 9},
            },
        },
        'rows': [
            {
                'area': (400, 170, 900, 260),
                'index': 1,
                'select_area': (760, 180, 880, 250),
                'selected': True,
            },
            {
                'area': (400, 274, 900, 364),
                'index': 2,
                'select_area': (760, 284, 880, 354),
                'selected': False,
            },
            {
                'area': (400, 378, 900, 468),
                'index': 3,
                'select_area': (760, 388, 880, 458),
                'selected': False,
            },
            {
                'area': (400, 482, 900, 572),
                'index': 4,
                'select_area': (760, 492, 880, 562),
                'selected': False,
            },
        ],
    }


@image('island/transport/ea8b4b22', server='jp')
def test_rewards_selected_third_jp(main: IslandTransport):
    assert list_snapshot(main, 'rewards') == {
        'readings': {
            1: {
                'amounts': [7, 24, 0],
                'items': {2604: 24, 2702: 7},
            },
            2: {
                'amounts': [29, 32, 0],
                'items': {2016: 29, 2701: 32},
            },
            3: {
                'amounts': [13, 42, 0],
                'items': {2601: 42, 2703: 13},
            },
            4: {
                'amounts': [9, 3, 0],
                'items': {2605: 3, 2702: 9},
            },
        },
        'rows': [
            {
                'area': (400, 170, 900, 260),
                'index': 1,
                'select_area': (760, 180, 880, 250),
                'selected': False,
            },
            {
                'area': (400, 274, 900, 364),
                'index': 2,
                'select_area': (760, 284, 880, 354),
                'selected': False,
            },
            {
                'area': (400, 378, 900, 468),
                'index': 3,
                'select_area': (760, 388, 880, 458),
                'selected': True,
            },
            {
                'area': (400, 482, 900, 572),
                'index': 4,
                'select_area': (760, 492, 880, 562),
                'selected': False,
            },
        ],
    }


@image('island/transport/2f538b0b', server='jp')
def test_sparse_requirements_jp(main: IslandTransport):
    assert list_snapshot(main, 'requirements') == {
        'readings': {
            1: {
                'items': [(2019, 20), (5108, 1)],
                'stock': {2019: 32, 5108: 13},
                'unknown': False,
            },
            2: {
                'items': [(5008, 12)],
                'stock': {5008: 23},
                'unknown': False,
            },
            6: {
                'items': [(2703, 26)],
                'stock': {2703: 138},
                'unknown': False,
            },
        },
        'rows': [
            {
                'area': (400, 170, 900, 260),
                'index': 1,
                'select_area': (760, 180, 880, 250),
                'selected': True,
            },
            {
                'area': (400, 274, 900, 364),
                'index': 2,
                'select_area': (760, 284, 880, 354),
                'selected': False,
            },
            {
                'area': (400, 378, 900, 468),
                'index': 6,
                'select_area': (760, 388, 880, 458),
                'selected': False,
            },
        ],
    }


@image('island/transport/768b0bf7', server='jp')
def test_sparse_rewards_jp(main: IslandTransport):
    assert list_snapshot(main, 'rewards') == {
        'readings': {
            1: {
                'amounts': [11, 10, 0],
                'items': {2022: 11, 2703: 10},
            },
            2: {
                'amounts': [16, 5, 3],
                'items': {2007: 3, 2521: 16, 2703: 5},
            },
            6: {
                'amounts': [23, 15, 0],
                'items': {2014: 15, 2801: 23},
            },
        },
        'rows': [
            {
                'area': (400, 170, 900, 260),
                'index': 1,
                'select_area': (760, 180, 880, 250),
                'selected': True,
            },
            {
                'area': (400, 274, 900, 364),
                'index': 2,
                'select_area': (760, 284, 880, 354),
                'selected': False,
            },
            {
                'area': (400, 378, 900, 468),
                'index': 6,
                'select_area': (760, 388, 880, 458),
                'selected': False,
            },
        ],
    }


@image('island/transport/536dd606', server='cn')
def test_requirements_selected_cn(main: IslandTransport):
    assert main.transport_refresh_status() == ('ready', None)
    main.device.review({'refresh_state': 'ready'}, [
        (ISLAND_TRANSPORT_LIST_REFRESH.area, 'list refresh ready'),
    ])
    assert list_snapshot(main, 'requirements') == {
        'readings': {
            1: {
                'items': [(2009, 44), (2702, 6)],
                'stock': {2009: 173, 2702: 0},
                'unknown': False,
            },
            2: {
                'items': [(5101, 12), (2018, 42)],
                'stock': {2018: 95, 5101: 0},
                'unknown': False,
            },
            3: {
                'items': [(2703, 17), (2601, 17), (2007, 3)],
                'stock': {2007: 211, 2601: 36355, 2703: 26},
                'unknown': False,
            },
            4: {
                'items': [(2601, 29), (2522, 8)],
                'stock': {2522: 15, 2601: 36355},
                'unknown': False,
            },
        },
        'rows': [
            {
                'area': (400, 170, 900, 260),
                'index': 1,
                'select_area': (760, 180, 880, 250),
                'selected': True,
            },
            {
                'area': (400, 274, 900, 364),
                'index': 2,
                'select_area': (760, 284, 880, 354),
                'selected': False,
            },
            {
                'area': (400, 378, 900, 468),
                'index': 3,
                'select_area': (760, 388, 880, 458),
                'selected': False,
            },
            {
                'area': (400, 482, 900, 572),
                'index': 4,
                'select_area': (760, 492, 880, 562),
                'selected': False,
            },
        ],
    }


@image('island/transport/6dad8956', server='cn')
def test_rewards_selected_cn(main: IslandTransport):
    assert list_snapshot(main, 'rewards') == {
        'readings': {
            1: {
                'amounts': [29, 3, 0],
                'items': {2605: 3, 2701: 29},
            },
            2: {
                'amounts': [11, 5, 8],
                'items': {2014: 8, 2022: 11, 2521: 5},
            },
            3: {
                'amounts': [27, 10, 1],
                'items': {2012: 10, 2605: 1, 5006: 27},
            },
            4: {
                'amounts': [39, 2, 14],
                'items': {2009: 14, 2018: 39, 2802: 2},
            },
        },
        'rows': [
            {
                'area': (400, 170, 900, 260),
                'index': 1,
                'select_area': (760, 180, 880, 250),
                'selected': True,
            },
            {
                'area': (400, 274, 900, 364),
                'index': 2,
                'select_area': (760, 284, 880, 354),
                'selected': False,
            },
            {
                'area': (400, 378, 900, 468),
                'index': 3,
                'select_area': (760, 388, 880, 458),
                'selected': False,
            },
            {
                'area': (400, 482, 900, 572),
                'index': 4,
                'select_area': (760, 492, 880, 562),
                'selected': False,
            },
        ],
    }
