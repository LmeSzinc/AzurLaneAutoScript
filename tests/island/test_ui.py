"""Screenshot golden results; awaiting human review of collection/ images."""
from module.testing.screenshot import image

from module.island.ui import IslandUI


class TestManageJP:
    @image('island/ui/cfa74ae7', server='jp')
    def test_first_manage_tab_selected(self, main: IslandUI):
        navbar = main._island_manage_side_navbar
        info = navbar.get_info(main=main)
        actual = dict(navbar=info, white_band=main.has_white_band(),
                      selected=[main.is_button_selected(button) for button in navbar.grids.buttons])
        regions = [(button.area, 'nav #{} selected={}'.format(index, actual['selected'][index]))
                   for index, button in enumerate(navbar.grids.buttons)]
        regions += [((0, 405, 1280, 560), 'white_band={}'.format(actual['white_band']))]
        main.device.review(actual, regions)
        assert actual == {'navbar': (0, 0, 2), 'selected': [True, False, False], 'white_band': False}

    @image('island/ui/826f8605', server='jp')
    def test_third_manage_tab_selected(self, main: IslandUI):
        navbar = main._island_manage_side_navbar
        info = navbar.get_info(main=main)
        actual = dict(navbar=info, white_band=main.has_white_band(),
                      selected=[main.is_button_selected(button) for button in navbar.grids.buttons])
        regions = [(button.area, 'nav #{} selected={}'.format(index, actual['selected'][index]))
                   for index, button in enumerate(navbar.grids.buttons)]
        regions += [((0, 405, 1280, 560), 'white_band={}'.format(actual['white_band']))]
        main.device.review(actual, regions)
        assert actual == {'navbar': (2, 0, 2), 'selected': [False, False, True], 'white_band': False}

    @image('island/ui/041ca368', server='jp')
    def test_manage_page_with_white_band(self, main: IslandUI):
        navbar = main._island_manage_side_navbar
        info = navbar.get_info(main=main)
        actual = dict(navbar=info, white_band=main.has_white_band(),
                      selected=[main.is_button_selected(button) for button in navbar.grids.buttons])
        regions = [(button.area, 'nav #{} selected={}'.format(index, actual['selected'][index]))
                   for index, button in enumerate(navbar.grids.buttons)]
        regions += [((0, 405, 1280, 560), 'white_band={}'.format(actual['white_band']))]
        main.device.review(actual, regions)
        assert actual == {'navbar': (None, 0, 1), 'selected': [False, False, False], 'white_band': True}
