"""Screenshot recognition coverage for island material collection."""

from module.testing.screenshot import image

from module.island.collect import IslandCollect
from module.island.assets import ISLAND_COLLECT_LOCATION_1, ISLAND_COLLECT_LOCATION_2


LOCATION_BUTTONS = (ISLAND_COLLECT_LOCATION_1, ISLAND_COLLECT_LOCATION_2)


class TestLocationSelectionJP:
    @image('island/collect/5081d7cc', server='jp')
    def test_both_collect_locations_unselected(self, main: IslandCollect):
        selected = [main.is_button_selected(button) for button in LOCATION_BUTTONS]
        unselected = main.collect_location_unselected_buttons()
        actual = {
            'selected': selected,
            'unselected': [button.area for button in unselected],
        }
        regions = [
            (button.area, 'collect location #{} selected={}'.format(index, selected[index]))
            for index, button in enumerate(LOCATION_BUTTONS)
        ]
        main.device.review(actual, regions)
        assert actual == {
            'selected': [False, False],
            'unselected': [(431, 216, 608, 466), (672, 216, 849, 466)],
        }

    @image('island/collect/99fd267e', server='jp')
    def test_both_collect_locations_selected(self, main: IslandCollect):
        selected = [main.is_button_selected(button) for button in LOCATION_BUTTONS]
        unselected = main.collect_location_unselected_buttons()
        actual = {
            'selected': selected,
            'unselected': [button.area for button in unselected],
        }
        regions = [
            (button.area, 'collect location #{} selected={}'.format(index, selected[index]))
            for index, button in enumerate(LOCATION_BUTTONS)
        ]
        main.device.review(actual, regions)
        assert actual == {
            'selected': [True, True],
            'unselected': [],
        }
