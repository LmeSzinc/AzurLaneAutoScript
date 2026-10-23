"""Recipe recognition goldens; awaiting human review of collection/ images."""
import pytest

from module.testing.screenshot import image

from module.island_handler.recipe import (
    IslandRecipe, ISLAND_RECIPE_AMOUNT_OCR, RECIPE_PRODUCT_NAME_OCR,
)


@pytest.fixture(autouse=True)
def recipe_ocr_language(request, monkeypatch):
    """Select real models for OCR objects whose language was fixed at import time."""
    server = request.function.__screenshot_server__
    name_language = server if server in ('jp', 'tw') else 'cnocr'
    amount_language = 'azur_lane_jp' if server == 'jp' else 'azur_lane'
    monkeypatch.setattr(RECIPE_PRODUCT_NAME_OCR, 'lang', name_language)
    monkeypatch.setattr(ISLAND_RECIPE_AMOUNT_OCR, 'lang', amount_language)


class TestRecipesCN:
    @image('island/recipe/661dfab1', server='cn')
    def test_first_recipe_with_two_ingredients(self, main: IslandRecipe):
        # Seed only the detected grid; all recognition still reads the unmodified screenshot.
        main.recipe_grid = main.get_recipe_grid()
        recipe_ids = main.get_recipe_ids()
        stocks = main.get_recipe_product_stocks()
        actual = dict(
            in_menu=main.is_in_recipe_menu(),
            recipes=[dict(area=button.area, recipe_id=recipe_id, stock=stock,
                          selected=main.is_button_selected(button))
                     for button, recipe_id, stock in zip(main.recipe_grid.buttons, recipe_ids, stocks)],
            active_recipe_id=main.get_active_recipe_id(),
            ingredients=main.get_recipe_ingredient_counters(),
            amount=ISLAND_RECIPE_AMOUNT_OCR.ocr(main.device.image),
            remaining_seconds=None,
        )
        remaining = main.get_recipe_remain_time()
        actual['remaining_seconds'] = remaining.total_seconds() if remaining is not None else None
        regions = [(entry['area'], 'recipe #{} id={} stock={} selected={}'.format(
            index, entry['recipe_id'], entry['stock'], entry['selected']))
            for index, entry in enumerate(actual['recipes'])]
        ingredient_grid = main.get_recipe_ingredient_grids()
        if ingredient_grid is not None:
            regions += [(button.area, 'ingredient #{} counter={}'.format(index, counter))
                        for index, (button, counter) in enumerate(zip(ingredient_grid.buttons, actual['ingredients']))]
        regions += [(ISLAND_RECIPE_AMOUNT_OCR.buttons[0], 'amount={}'.format(actual['amount']))]
        main.device.review(actual, regions)
        assert actual == {
            'active_recipe_id': 9900021,
            'amount': 1,
            'in_menu': True,
            'ingredients': [(52, 4, 48), (33416, 6, 33410)],
            'recipes': [
                {
                    'area': (181, 114, 461, 248),
                    'recipe_id': 9900021,
                    'selected': True,
                    'stock': 40,
                },
                {
                    'area': (181, 263, 461, 397),
                    'recipe_id': 9900022,
                    'selected': False,
                    'stock': 3,
                },
                {
                    'area': (181, 412, 461, 546),
                    'recipe_id': 601001,
                    'selected': False,
                    'stock': 101,
                },
            ],
            'remaining_seconds': 1800.0,
        }

    @image('island/recipe/0e57ef95', server='cn')
    def test_single_recipe_without_ingredients(self, main: IslandRecipe):
        # Seed only the detected grid; all recognition still reads the unmodified screenshot.
        main.recipe_grid = main.get_recipe_grid()
        recipe_ids = main.get_recipe_ids()
        stocks = main.get_recipe_product_stocks()
        actual = dict(
            in_menu=main.is_in_recipe_menu(),
            recipes=[dict(area=button.area, recipe_id=recipe_id, stock=stock,
                          selected=main.is_button_selected(button))
                     for button, recipe_id, stock in zip(main.recipe_grid.buttons, recipe_ids, stocks)],
            active_recipe_id=main.get_active_recipe_id(),
            ingredients=main.get_recipe_ingredient_counters(),
            amount=ISLAND_RECIPE_AMOUNT_OCR.ocr(main.device.image),
            remaining_seconds=None,
        )
        remaining = main.get_recipe_remain_time()
        actual['remaining_seconds'] = remaining.total_seconds() if remaining is not None else None
        regions = [(entry['area'], 'recipe #{} id={} stock={} selected={}'.format(
            index, entry['recipe_id'], entry['stock'], entry['selected']))
            for index, entry in enumerate(actual['recipes'])]
        ingredient_grid = main.get_recipe_ingredient_grids()
        if ingredient_grid is not None:
            regions += [(button.area, 'ingredient #{} counter={}'.format(index, counter))
                        for index, (button, counter) in enumerate(zip(ingredient_grid.buttons, actual['ingredients']))]
        regions += [(ISLAND_RECIPE_AMOUNT_OCR.buttons[0], 'amount={}'.format(actual['amount']))]
        main.device.review(actual, regions)
        assert actual == {
            'active_recipe_id': 402004,
            'amount': 2,
            'in_menu': True,
            'ingredients': [],
            'recipes': [
                {
                    'area': (181, 114, 461, 248),
                    'recipe_id': 402004,
                    'selected': True,
                    'stock': 2912,
                },
            ],
            'remaining_seconds': 17142.0,
        }


class TestRecipesEN:
    @image('island/recipe/ec1f31d3', server='en')
    def test_third_recipe_with_two_ingredients(self, main: IslandRecipe):
        # Seed only the detected grid; all recognition still reads the unmodified screenshot.
        main.recipe_grid = main.get_recipe_grid()
        recipe_ids = main.get_recipe_ids()
        stocks = main.get_recipe_product_stocks()
        actual = dict(
            in_menu=main.is_in_recipe_menu(),
            recipes=[dict(area=button.area, recipe_id=recipe_id, stock=stock,
                          selected=main.is_button_selected(button))
                     for button, recipe_id, stock in zip(main.recipe_grid.buttons, recipe_ids, stocks)],
            active_recipe_id=main.get_active_recipe_id(),
            ingredients=main.get_recipe_ingredient_counters(),
            amount=ISLAND_RECIPE_AMOUNT_OCR.ocr(main.device.image),
            remaining_seconds=None,
        )
        remaining = main.get_recipe_remain_time()
        actual['remaining_seconds'] = remaining.total_seconds() if remaining is not None else None
        regions = [(entry['area'], 'recipe #{} id={} stock={} selected={}'.format(
            index, entry['recipe_id'], entry['stock'], entry['selected']))
            for index, entry in enumerate(actual['recipes'])]
        ingredient_grid = main.get_recipe_ingredient_grids()
        if ingredient_grid is not None:
            regions += [(button.area, 'ingredient #{} counter={}'.format(index, counter))
                        for index, (button, counter) in enumerate(zip(ingredient_grid.buttons, actual['ingredients']))]
        regions += [(ISLAND_RECIPE_AMOUNT_OCR.buttons[0], 'amount={}'.format(actual['amount']))]
        main.device.review(actual, regions)
        assert actual == {
            'active_recipe_id': 901102,
            'amount': 1,
            'in_menu': True,
            'ingredients': [(77, 1, 76), (50, 1, 49)],
            'recipes': [
                {
                    'area': (181, 71, 461, 205),
                    'recipe_id': 901006,
                    'selected': False,
                    'stock': 12,
                },
                {
                    'area': (181, 220, 461, 354),
                    'recipe_id': 901101,
                    'selected': False,
                    'stock': 0,
                },
                {
                    'area': (181, 369, 461, 503),
                    'recipe_id': 901102,
                    'selected': True,
                    'stock': 0,
                },
                {
                    'area': (181, 518, 461, 652),
                    'recipe_id': 901103,
                    'selected': False,
                    'stock': 0,
                },
            ],
            'remaining_seconds': 600.0,
        }


class TestRecipesJP:
    @image('island/recipe/2ebb5c8e', server='jp')
    def test_first_recipe_with_two_ingredients(self, main: IslandRecipe):
        # Seed only the detected grid; all recognition still reads the unmodified screenshot.
        main.recipe_grid = main.get_recipe_grid()
        recipe_ids = main.get_recipe_ids()
        stocks = main.get_recipe_product_stocks()
        actual = dict(
            in_menu=main.is_in_recipe_menu(),
            recipes=[dict(area=button.area, recipe_id=recipe_id, stock=stock,
                          selected=main.is_button_selected(button))
                     for button, recipe_id, stock in zip(main.recipe_grid.buttons, recipe_ids, stocks)],
            active_recipe_id=main.get_active_recipe_id(),
            ingredients=main.get_recipe_ingredient_counters(),
            amount=ISLAND_RECIPE_AMOUNT_OCR.ocr(main.device.image),
            remaining_seconds=None,
        )
        remaining = main.get_recipe_remain_time()
        actual['remaining_seconds'] = remaining.total_seconds() if remaining is not None else None
        regions = [(entry['area'], 'recipe #{} id={} stock={} selected={}'.format(
            index, entry['recipe_id'], entry['stock'], entry['selected']))
            for index, entry in enumerate(actual['recipes'])]
        ingredient_grid = main.get_recipe_ingredient_grids()
        if ingredient_grid is not None:
            regions += [(button.area, 'ingredient #{} counter={}'.format(index, counter))
                        for index, (button, counter) in enumerate(zip(ingredient_grid.buttons, actual['ingredients']))]
        regions += [(ISLAND_RECIPE_AMOUNT_OCR.buttons[0], 'amount={}'.format(actual['amount']))]
        main.device.review(actual, regions)
        assert actual == {
            'active_recipe_id': 9900021,
            'amount': 1,
            'in_menu': True,
            'ingredients': [(112, 4, 108), (50, 6, 44)],
            'recipes': [
                {
                    'area': (181, 114, 461, 248),
                    'recipe_id': 9900021,
                    'selected': True,
                    'stock': 0,
                },
                {
                    'area': (181, 263, 461, 397),
                    'recipe_id': 9900022,
                    'selected': False,
                    'stock': 0,
                },
                {
                    'area': (181, 412, 461, 546),
                    'recipe_id': 601001,
                    'selected': False,
                    'stock': 0,
                },
            ],
            'remaining_seconds': 1800.0,
        }
