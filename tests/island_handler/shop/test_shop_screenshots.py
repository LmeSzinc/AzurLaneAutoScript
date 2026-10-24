"""Screenshot golden results; awaiting human review of collection/ images."""
from module.testing.screenshot import image

from module.island_handler.shop import IslandShop
from module.island_handler.assets import ISLAND_SHOP_BUY_AMOUNT
from module.ocr.ocr import Digit


class TestProductsJP:
    @image('island/shop/9a4f9204', server='jp')
    def test_product_names_and_currency(self, main: IslandShop):
        names = main._island_shop_item_name_ocr.ocr(main.device.image)
        actual = dict(names=names, recipe_ids=main.island_shop_get_item_ids(),
                      currency=main.island_shop_get_currency())
        regions = [(button.area, 'product #{} recipe={}'.format(index, actual['recipe_ids'][index]))
                   for index, button in enumerate(main._island_shop_item_grid.buttons)]
        regions += [(button.area, 'currency #{}'.format(index))
                    for index, button in enumerate(main._island_currency_grid.buttons)]
        main.device.review(actual, regions)
        assert actual == {
            'currency': {2000: 364, 2001: 1784, 2008: 966},
            'names': ['コッコートリの', 'ブーブーブタの', 'モ一モ一ウシの', 'メェメーヒツジ', '小麦粉', '', '', '', '', '', '', ''],
            'recipe_ids': [103000, 103001, 103002, 103003, 103004, None, None, None, None, None, None, None],
        }


class TestPurchaseJP:
    @image('island/shop/05ea6704', server='jp')
    def test_single_purchase_amount(self, main: IslandShop):
        amount = Digit(ISLAND_SHOP_BUY_AMOUNT, lang='azur_lane', letter=(57, 58, 60), threshold=160,
                       name='island_shop_buy_amount_ocr').ocr(main.device.image)
        actual = dict(amount=amount, white_band=main.has_white_band())
        regions = [(ISLAND_SHOP_BUY_AMOUNT.area, 'buy amount={}'.format(amount))]
        main.device.review(actual, regions)
        assert actual == {'amount': 1, 'white_band': False}


class TestPurchaseCN:
    @image('island/shop/17d9b4e7', server='cn')
    def test_large_purchase_amount(self, main: IslandShop):
        amount = Digit(ISLAND_SHOP_BUY_AMOUNT, lang='cnocr', letter=(57, 58, 60), threshold=160,
                       name='island_shop_buy_amount_ocr').ocr(main.device.image)
        actual = dict(amount=amount, white_band=main.has_white_band())
        regions = [(ISLAND_SHOP_BUY_AMOUNT.area, 'buy amount={}'.format(amount))]
        main.device.review(actual, regions)
        assert actual == {'amount': 107, 'white_band': False}
