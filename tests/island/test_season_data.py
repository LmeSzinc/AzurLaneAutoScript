from copy import deepcopy

import pytest

import module.config.server as server
from module.island import utils
from module.island.data import DIC_ISLAND_RECIPE, DIC_ISLAND_SLOT
from module.island.season_data import DIC_ISLAND_SEASON
from module.island_handler.recipe import recipe_product_name_to_recipe_id


def test_slot_catalog_keeps_older_recipes_without_enabling_them():
    autumn = DIC_ISLAND_SEASON['season_20260806_cn']
    winter = DIC_ISLAND_SEASON['season_20261105_cn']

    assert 9900003 in utils.get_slot_recipe_ids(9061, autumn)
    assert 9900027 not in utils.get_slot_recipe_ids(9061, autumn)
    assert 9900027 in utils.get_slot_recipe_ids(9061, winter)
    assert 9900003 not in utils.get_slot_recipe_ids(9061, winter)
    assert {9900003, 9900027} <= set(utils.get_slot_recipe_ids(9061, None, include_inactive=True))
    assert utils.get_slot_recipe_ids(9061, None) == DIC_ISLAND_SLOT[9061]['formula']


@pytest.mark.parametrize(('name', 'recipe_id'), [('柿子餅', 9900003), ('松茸雞湯', 9900004)])
def test_tw_recipe_ocr_recognizes_older_slot_recipes(monkeypatch, name, recipe_id):
    monkeypatch.setattr(server, 'server', 'tw')

    assert recipe_product_name_to_recipe_id(name, slotcode=9061) == recipe_id


def test_current_cn_and_tw_recipe_values(monkeypatch):
    permanent = deepcopy(DIC_ISLAND_RECIPE[9900001])
    monkeypatch.setattr(server, 'server', 'tw')

    assert utils.get_recipe_data(9900001)['commission_cost'] == {4006: 1}
    assert utils.get_recipe_data(9900001)['commission_product'] == {4005: 8}
    assert utils.get_recipe_data(9900003)['production_limit'] == 5
    assert DIC_ISLAND_RECIPE[9900001] == permanent

    monkeypatch.setattr(server, 'server', 'cn')
    assert utils.get_recipe_data(9900001)['commission_cost'] == {4006: 4}
    assert utils.get_recipe_data(9900001)['commission_product'] == {4005: 32}
    assert utils.get_recipe_data(9900003)['production_limit'] == 8


def test_dependency_lookup_uses_the_selected_season():
    season = {'ingredient_source_slots': {9061: [9101]}}

    assert utils.get_slot_ingredient_source_slots(9061, season) == [9101]
    assert utils.get_slot_ingredient_source_slots(9031, season) == DIC_ISLAND_SLOT[9031]['ingredient_source_slots']


def test_order_requirements_use_the_shared_order_catalog():
    assert utils.get_stuck_season_order_requirements(100014) == {
        4010: 5, 4012: 5, 4011: 5, 4013: 5,
    }
