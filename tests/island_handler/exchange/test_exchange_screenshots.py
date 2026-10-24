"""Exchange recognition goldens; awaiting human review of collection/ images."""
from module.testing.screenshot import image

from module.island_handler.exchange import (
    EXCHANGE_FISH_GRID, IslandExchange, read_fish_cards, read_fish_counts, read_fish_meat,
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
