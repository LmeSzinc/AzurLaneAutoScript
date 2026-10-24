"""Screenshot golden results; awaiting human review of collection/ images."""
from module.testing.screenshot import image

from module.island.production import IslandProduction


class TestOverviewJP:
    @image('island/production/1c0c7115', server='jp')
    def test_overview_with_finished_slots(self, main: IslandProduction):
        # The uncached reader describes this frame without entering a screenshot retry loop.
        main.production_grid = main.get_production_grid()
        names = main.get_production_codename()
        actual = dict(
            places=[dict(area=button.area, place_id=place_id)
                    for button, place_id in zip(main.production_grid.buttons, names)],
            slots={place_id: [dict(area=button.area, finished=main.is_slot_finished(button),
                                   empty=main.is_slot_empty(button)) for button in grid.buttons]
                   for place_id, grid in main.get_production_slot_grids().items()},
            enter_window=main.is_enter_window_shown(),
        )
        regions = [(entry['area'], 'place #{} id={}'.format(index, entry['place_id']))
                   for index, entry in enumerate(actual['places'])]
        regions += [(entry['area'], '{} #{} finished={} empty={}'.format(
                        place_id, index, entry['finished'], entry['empty']))
                    for place_id, entries in actual['slots'].items() for index, entry in enumerate(entries)]
        main.device.review(actual, regions)
        assert actual == {
            'enter_window': False,
            'places': [
                {'area': (192, 86, 682, 245), 'place_id': 602},
                {'area': (731, 86, 1221, 245), 'place_id': 603},
                {'area': (192, 270, 682, 429), 'place_id': 604},
                {'area': (731, 270, 1221, 429), 'place_id': 703},
                {'area': (192, 453, 682, 612), 'place_id': 704},
                {'area': (731, 453, 1221, 612), 'place_id': 705},
            ],
            'slots': {
                602: [
                    {'area': (254, 145, 340, 231), 'empty': False, 'finished': True},
                    {'area': (349, 145, 435, 231), 'empty': False, 'finished': True},
                ],
                603: [
                    {'area': (793, 145, 879, 231), 'empty': False, 'finished': False},
                    {'area': (888, 145, 974, 231), 'empty': False, 'finished': False},
                ],
                604: [
                    {'area': (254, 329, 340, 415), 'empty': False, 'finished': False},
                    {'area': (349, 329, 435, 415), 'empty': False, 'finished': False},
                ],
                703: [
                    {'area': (793, 329, 879, 415), 'empty': False, 'finished': False},
                    {'area': (888, 329, 974, 415), 'empty': False, 'finished': False},
                ],
                704: [
                    {'area': (254, 512, 340, 598), 'empty': False, 'finished': False},
                    {'area': (349, 512, 435, 598), 'empty': False, 'finished': False},
                ],
                705: [
                    {'area': (793, 512, 879, 598), 'empty': False, 'finished': False},
                    {'area': (888, 512, 974, 598), 'empty': False, 'finished': False},
                ],
            },
        }

    @image('island/production/d6951043', server='jp')
    def test_overview_with_empty_slots(self, main: IslandProduction):
        # The uncached reader describes this frame without entering a screenshot retry loop.
        main.production_grid = main.get_production_grid()
        names = main.get_production_codename()
        actual = dict(
            places=[dict(area=button.area, place_id=place_id)
                    for button, place_id in zip(main.production_grid.buttons, names)],
            slots={place_id: [dict(area=button.area, finished=main.is_slot_finished(button),
                                   empty=main.is_slot_empty(button)) for button in grid.buttons]
                   for place_id, grid in main.get_production_slot_grids().items()},
            enter_window=main.is_enter_window_shown(),
        )
        regions = [(entry['area'], 'place #{} id={}'.format(index, entry['place_id']))
                   for index, entry in enumerate(actual['places'])]
        regions += [(entry['area'], '{} #{} finished={} empty={}'.format(
                        place_id, index, entry['finished'], entry['empty']))
                    for place_id, entries in actual['slots'].items() for index, entry in enumerate(entries)]
        main.device.review(actual, regions)
        assert actual == {
            'enter_window': True,
            'places': [
                {'area': (192, 70, 682, 229), 'place_id': 101},
                {'area': (731, 70, 1221, 229), 'place_id': 102},
                {'area': (192, 254, 682, 413), 'place_id': 201},
                {'area': (731, 254, 1221, 413), 'place_id': None},
                {'area': (192, 437, 682, 596), 'place_id': 402},
                {'area': (731, 437, 1221, 596), 'place_id': None},
            ],
            'slots': {
                101: [
                    {'area': (254, 129, 340, 215), 'empty': False, 'finished': True},
                    {'area': (349, 129, 435, 215), 'empty': False, 'finished': True},
                    {'area': (443, 129, 529, 215), 'empty': False, 'finished': True},
                    {'area': (538, 129, 624, 215), 'empty': False, 'finished': False},
                ],
                102: [
                    {'area': (793, 129, 879, 215), 'empty': False, 'finished': True},
                    {'area': (888, 129, 974, 215), 'empty': False, 'finished': True},
                    {'area': (982, 129, 1068, 215), 'empty': False, 'finished': True},
                    {'area': (1077, 129, 1163, 215), 'empty': False, 'finished': True},
                ],
                201: [
                    {'area': (254, 313, 340, 399), 'empty': False, 'finished': True},
                    {'area': (349, 313, 435, 399), 'empty': False, 'finished': True},
                    {'area': (443, 313, 529, 399), 'empty': True, 'finished': False},
                ],
                402: [
                    {'area': (254, 496, 340, 582), 'empty': False, 'finished': True},
                    {'area': (349, 496, 435, 582), 'empty': False, 'finished': True},
                    {'area': (443, 496, 529, 582), 'empty': False, 'finished': True},
                    {'area': (538, 496, 624, 582), 'empty': False, 'finished': False},
                ],
            },
        }


class TestOverviewCN:
    @image('island/production/0adb2438', server='cn')
    def test_overview_with_finished_slots(self, main: IslandProduction):
        # The uncached reader describes this frame without entering a screenshot retry loop.
        main.production_grid = main.get_production_grid()
        names = main.get_production_codename()
        actual = dict(
            places=[dict(area=button.area, place_id=place_id)
                    for button, place_id in zip(main.production_grid.buttons, names)],
            slots={place_id: [dict(area=button.area, finished=main.is_slot_finished(button),
                                   empty=main.is_slot_empty(button)) for button in grid.buttons]
                   for place_id, grid in main.get_production_slot_grids().items()},
            enter_window=main.is_enter_window_shown(),
        )
        regions = [(entry['area'], 'place #{} id={}'.format(index, entry['place_id']))
                   for index, entry in enumerate(actual['places'])]
        regions += [(entry['area'], '{} #{} finished={} empty={}'.format(
                        place_id, index, entry['finished'], entry['empty']))
                    for place_id, entries in actual['slots'].items() for index, entry in enumerate(entries)]
        main.device.review(actual, regions)
        assert actual == {
            'enter_window': False,
            'places': [
                {'area': (192, 123, 682, 282), 'place_id': 604},
                {'area': (731, 123, 1221, 282), 'place_id': 703},
                {'area': (192, 306, 682, 465), 'place_id': 704},
                {'area': (731, 306, 1221, 465), 'place_id': 705},
                {'area': (192, 490, 682, 649), 'place_id': 706},
                {'area': (731, 490, 1221, 649), 'place_id': 901},
            ],
            'slots': {
                604: [
                    {'area': (254, 182, 340, 268), 'empty': False, 'finished': False},
                    {'area': (349, 182, 435, 268), 'empty': False, 'finished': False},
                ],
                703: [
                    {'area': (793, 182, 879, 268), 'empty': False, 'finished': False},
                    {'area': (888, 182, 974, 268), 'empty': False, 'finished': False},
                ],
                704: [
                    {'area': (254, 365, 340, 451), 'empty': False, 'finished': False},
                    {'area': (349, 365, 435, 451), 'empty': False, 'finished': False},
                ],
                705: [
                    {'area': (793, 365, 879, 451), 'empty': False, 'finished': False},
                    {'area': (888, 365, 974, 451), 'empty': False, 'finished': False},
                ],
                706: [
                    {'area': (254, 549, 340, 635), 'empty': False, 'finished': True},
                    {'area': (349, 549, 435, 635), 'empty': False, 'finished': True},
                ],
                901: [
                    {'area': (793, 549, 879, 635), 'empty': False, 'finished': True},
                    {'area': (888, 549, 974, 635), 'empty': False, 'finished': True},
                ],
            },
        }
