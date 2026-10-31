"""Exchange recognition goldens; awaiting human review of collection/ images."""
from module.testing.screenshot import image

from module.base.utils import crop
from module.island_handler.exchange import (
    EXCHANGE_FISH_GRID, EXCHANGE_FISH_ICON_GRID, EXCHANGE_FISH_TEMPLATES,
    IslandExchange, fish_icon_to_id, read_fish_cards, read_fish_counts, read_fish_meat,
)
from module.island_handler.assets import ISLAND_EXCHANGE_TOTAL_AMOUNT


class TestCardsJP:
    @image('island/exchange/272a0fc0', server='jp')
    def test_five_unselected_fish_cards(self, main: IslandExchange):
        cards = read_fish_cards(main.device.image, 2522)
        counts = read_fish_counts(main.device.image, list(range(len(EXCHANGE_FISH_GRID.buttons))))
        actual = dict(cards=cards, counts=counts, meat=read_fish_meat(main.device.image))
        regions = [(button.area, 'card #{} selected={}'.format(index, counts[index]))
                   for index, button in enumerate(EXCHANGE_FISH_GRID.buttons)]
        regions += [(ISLAND_EXCHANGE_TOTAL_AMOUNT.area, 'meat owned={} gain={}'.format(*actual['meat']))]
        main.device.review(actual, regions)
        assert actual == {
            'cards': [(0, 5103, 2), (1, 5104, 4), (2, 5105, 4), (3, 5106, 4), (4, 5107, 10)],
            'counts': [0, 0, 0, 0, 0, 0, 0, 0],
            'meat': (395, 0),
        }

    @image('island/exchange/42f1d138', server='jp')
    def test_two_unselected_fish_cards(self, main: IslandExchange):
        cards = read_fish_cards(main.device.image, 2522)
        counts = read_fish_counts(main.device.image, list(range(len(EXCHANGE_FISH_GRID.buttons))))
        actual = dict(cards=cards, counts=counts, meat=read_fish_meat(main.device.image))
        regions = [(button.area, 'card #{} selected={}'.format(index, counts[index]))
                   for index, button in enumerate(EXCHANGE_FISH_GRID.buttons)]
        regions += [(ISLAND_EXCHANGE_TOTAL_AMOUNT.area, 'meat owned={} gain={}'.format(*actual['meat']))]
        main.device.review(actual, regions)
        assert actual == {
            'cards': [(0, 5105, 4), (1, 5107, 2)],
            'counts': [0, 0, 0, 0, 0, 0, 0, 0],
            'meat': (398, 0),
        }

    @image('island/exchange/c7204940', server='jp')
    def test_single_unselected_fish_card_with_no_meat(self, main: IslandExchange):
        cards = read_fish_cards(main.device.image, 2521)
        counts = read_fish_counts(main.device.image, list(range(len(EXCHANGE_FISH_GRID.buttons))))
        actual = dict(cards=cards, counts=counts, meat=read_fish_meat(main.device.image))
        regions = [(button.area, 'card #{} selected={}'.format(index, counts[index]))
                   for index, button in enumerate(EXCHANGE_FISH_GRID.buttons)]
        regions += [(ISLAND_EXCHANGE_TOTAL_AMOUNT.area, 'meat owned={} gain={}'.format(*actual['meat']))]
        main.device.review(actual, regions)
        assert actual == {'cards': [(0, 5002, 2)], 'counts': [0, 0, 0, 0, 0, 0, 0, 0], 'meat': (0, 0)}

    @image('island/exchange/437cfb0e', server='jp')
    def test_single_unselected_fish_card_with_owned_meat(self, main: IslandExchange):
        cards = read_fish_cards(main.device.image, 2522)
        counts = read_fish_counts(main.device.image, list(range(len(EXCHANGE_FISH_GRID.buttons))))
        actual = dict(cards=cards, counts=counts, meat=read_fish_meat(main.device.image))
        regions = [(button.area, 'card #{} selected={}'.format(index, counts[index]))
                   for index, button in enumerate(EXCHANGE_FISH_GRID.buttons)]
        regions += [(ISLAND_EXCHANGE_TOTAL_AMOUNT.area, 'meat owned={} gain={}'.format(*actual['meat']))]
        main.device.review(actual, regions)
        assert actual == {'cards': [(0, 5107, 2)], 'counts': [0, 0, 0, 0, 0, 0, 0, 0], 'meat': (399, 0)}


class TestSelectionJP:
    @image('island/exchange/38c8558f', server='jp')
    def test_four_of_first_fish_selected(self, main: IslandExchange):
        counts = read_fish_counts(main.device.image, list(range(len(EXCHANGE_FISH_GRID.buttons))))
        actual = dict(counts=counts, meat=read_fish_meat(main.device.image))
        regions = [(button.area, 'card #{} selected={}'.format(index, counts[index]))
                   for index, button in enumerate(EXCHANGE_FISH_GRID.buttons)]
        regions += [(ISLAND_EXCHANGE_TOTAL_AMOUNT.area, 'meat owned={} gain={}'.format(*actual['meat']))]
        main.device.review(actual, regions)
        assert actual == {'counts': [4, 0, 0, 0, 0, 0, 0, 0], 'meat': (0, 4)}

    @image('island/exchange/ced8a5ba', server='jp')
    def test_one_of_first_fish_selected(self, main: IslandExchange):
        counts = read_fish_counts(main.device.image, list(range(len(EXCHANGE_FISH_GRID.buttons))))
        actual = dict(counts=counts, meat=read_fish_meat(main.device.image))
        regions = [(button.area, 'card #{} selected={}'.format(index, counts[index]))
                   for index, button in enumerate(EXCHANGE_FISH_GRID.buttons)]
        regions += [(ISLAND_EXCHANGE_TOTAL_AMOUNT.area, 'meat owned={} gain={}'.format(*actual['meat']))]
        main.device.review(actual, regions)
        assert actual == {'counts': [1, 0, 0, 0, 0, 0, 0, 0], 'meat': (399, 18)}

    @image('island/exchange/d40819a7', server='jp')
    def test_two_of_first_fish_selected(self, main: IslandExchange):
        counts = read_fish_counts(main.device.image, list(range(len(EXCHANGE_FISH_GRID.buttons))))
        actual = dict(counts=counts, meat=read_fish_meat(main.device.image))
        regions = [(button.area, 'card #{} selected={}'.format(index, counts[index]))
                   for index, button in enumerate(EXCHANGE_FISH_GRID.buttons)]
        regions += [(ISLAND_EXCHANGE_TOTAL_AMOUNT.area, 'meat owned={} gain={}'.format(*actual['meat']))]
        main.device.review(actual, regions)
        assert actual == {'counts': [2, 0, 0, 0, 0, 0, 0, 0], 'meat': (399, 36)}


class TestCardsCN:
    @image('island/exchange/fe39f9e0', server='cn')
    def test_no_fish_cards(self, main: IslandExchange):
        cards = read_fish_cards(main.device.image, 2522)
        counts = read_fish_counts(main.device.image, list(range(len(EXCHANGE_FISH_GRID.buttons))))
        actual = dict(cards=cards, counts=counts, meat=read_fish_meat(main.device.image))
        regions = [(button.area, 'card #{} selected={}'.format(index, counts[index]))
                   for index, button in enumerate(EXCHANGE_FISH_GRID.buttons)]
        regions += [(ISLAND_EXCHANGE_TOTAL_AMOUNT.area, 'meat owned={} gain={}'.format(*actual['meat']))]
        main.device.review(actual, regions)
        assert actual == {'cards': [], 'counts': [0, 0, 0, 0, 0, 0, 0, 0], 'meat': (0, 0)}


class TestCardsEN:
    @image('island/exchange/38cc331e', server='en')
    def test_six_unselected_saltwater_fish_cards(self, main: IslandExchange):
        cards = read_fish_cards(main.device.image, 2522)
        counts = read_fish_counts(main.device.image, list(range(len(EXCHANGE_FISH_GRID.buttons))))
        actual = dict(cards=cards, counts=counts, meat=read_fish_meat(main.device.image))
        regions = [(button.area, 'card #{} selected={}'.format(index, counts[index]))
                   for index, button in enumerate(EXCHANGE_FISH_GRID.buttons)]
        regions += [(ISLAND_EXCHANGE_TOTAL_AMOUNT.area, 'meat owned={} gain={}'.format(*actual['meat']))]
        main.device.review(actual, regions)
        assert actual == {
            'cards': [(0, 5102, 1), (1, 5103, 1), (2, 5104, 1), (3, 5105, 1), (4, 5106, 1), (5, 5107, 1)],
            'counts': [0, 0, 0, 0, 0, 0, 0, 0],
            'meat': (17791, 0),
        }

    @image('island/exchange/6892c695', server='en')
    def test_four_unselected_freshwater_fish_cards(self, main: IslandExchange):
        cards = read_fish_cards(main.device.image, 2521)
        counts = read_fish_counts(main.device.image, list(range(len(EXCHANGE_FISH_GRID.buttons))))
        actual = dict(cards=cards, counts=counts, meat=read_fish_meat(main.device.image))
        regions = [(button.area, 'card #{} selected={}'.format(index, counts[index]))
                   for index, button in enumerate(EXCHANGE_FISH_GRID.buttons)]
        regions += [(ISLAND_EXCHANGE_TOTAL_AMOUNT.area, 'meat owned={} gain={}'.format(*actual['meat']))]
        main.device.review(actual, regions)
        assert actual == {
            'cards': [(0, 5002, 1), (1, 5003, 1), (2, 5004, 1), (3, 5007, 1)],
            'counts': [0, 0, 0, 0, 0, 0, 0, 0],
            'meat': (40, 0),
        }


class TestFishIconToId:
    @image('island/exchange/38cc331e', server='en')
    def test_empty_card_is_not_a_fish(self, main: IslandExchange):
        icon = crop(main.device.image, EXCHANGE_FISH_ICON_GRID.buttons[7].area)
        assert fish_icon_to_id(icon, 2522) is None

    @image('island/exchange/38cc331e', server='en')
    def test_fish_from_other_meat_tab_is_rejected(self, main: IslandExchange):
        icon = crop(main.device.image, EXCHANGE_FISH_ICON_GRID.buttons[0].area)
        assert fish_icon_to_id(icon, 2521) is None

    @image('island/exchange/38cc331e', server='en')
    def test_ambiguous_icon_is_rejected(self, main: IslandExchange, monkeypatch):
        icon = crop(main.device.image, EXCHANGE_FISH_ICON_GRID.buttons[3].area)
        monkeypatch.setitem(EXCHANGE_FISH_TEMPLATES, 5106, EXCHANGE_FISH_TEMPLATES[5105])
        assert fish_icon_to_id(icon, 2522) is None
