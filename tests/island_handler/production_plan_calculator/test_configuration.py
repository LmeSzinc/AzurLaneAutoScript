import pytest

import module.config.server as server
from module.island.data import DIC_ISLAND_RECIPE
from module.island.season_data import (
    DIC_ISLAND_SEASON, DIC_ISLAND_SEASONAL_SHOP_GOODS,
)


class TestAnalyzeTechnologyStatus:
    def test_base_slots_with_empty_technology(self, make_calculator):
        calc = make_calculator({})
        # Slots available without any technology
        for slot in [9031, 9041, 9061, 9201, 9211]:
            assert calc.slot_available[slot], slot
        # Slots requiring technology
        for slot in [9001, 9011, 9021, 9032, 9042, 9062, 9203, 9212]:
            assert not calc.slot_available[slot], slot
        assert calc.ranch_level == {9031: 0, 9032: 0, 9033: 0, 9034: 0}
        assert not calc.mining_additional
        assert not calc.ranch_additional

    def test_technology_unlocks_slot_and_recipe(self, make_calculator):
        calc = make_calculator({310101: True, 410301: True, 410302: True, 500212: True})
        assert calc.slot_available[9001]
        assert not calc.slot_available[9002]
        assert calc.ranch_level[9031] == 2
        # 玉米 recipe gated by 500212
        assert calc.recipe_available[101002]
        # 牧草 recipe still locked
        assert not calc.recipe_available[101003]

    def test_recipe_available_defaults(self, make_calculator):
        calc = make_calculator({})
        # Ungated normal recipe defaults to available
        assert calc.recipe_available[101001]
        # Gated recipe defaults to locked
        assert not calc.recipe_available[101002]

    def test_wild_gather_availability(self, make_calculator):
        calc = make_calculator({})
        assert calc.wild_gather_available[1]
        # Gathers 5 and 6 are gated by technology
        assert not calc.wild_gather_available[5]
        assert not calc.wild_gather_available[6]
        # Activity gathers default to unavailable
        assert not calc.wild_gather_available[1001]
        calc = make_calculator({450301: True})
        assert calc.wild_gather_available[5]

    def test_selected_season_enables_seasonal_content(self, make_calculator):
        season = DIC_ISLAND_SEASON['season_20251106_cn']
        recipe_ids = {recipe_id for recipes in season['production'].values() for recipe_id in recipes}
        gather_ids = season['wild_gather']
        calc = make_calculator({}, season_name='season_20251106_cn')
        for recipe_id in recipe_ids:
            assert calc.recipe_available[recipe_id], recipe_id
        for gather_id in gather_ids:
            assert calc.wild_gather_available[gather_id], gather_id
        # The permanent catalog alone never enables a seasonal recipe.
        calc = make_calculator({})
        assert not any(
            calc.recipe_available.get(recipe_id, False)
            for recipe_id in recipe_ids
            if recipe_id not in calc.available_slot_recipes
        )

    def test_place_efficiency_bonus(self, make_calculator):
        calc = make_calculator({220601: True}, place_efficiency={101: 0.05, 501: None})
        assert calc.place_efficiency_bonus[101] == 0.05
        assert calc.place_efficiency_bonus[401] == 0.05
        assert calc.place_efficiency_bonus[402] == 0
        # None from config falls back to 0
        assert calc.place_efficiency_bonus[501] == 0


class TestRestaurantSettings:
    def test_default_settings_disable_restaurants(self, make_calculator):
        calc = make_calculator({})
        for restaurant_id in calc.restaurant_enabled:
            assert not calc.restaurant_enabled[restaurant_id]
        assert calc.restaurant_capacity[601] == 5  # bronze
        assert calc.restaurant_quantity[601] == 2
        assert calc.restaurant_sales_bonus[601] == 0
        assert calc.restaurant_grade[601] == 'bronze'
        assert calc.restaurant_waitress_slots[601] == ('none', 'none')

    def test_waitress_effects(self, make_calculator):
        calc = make_calculator({}, restaurant_settings={
            601: {'grade': 'gold', 'waitress_slots': ('Chao_Ho', 'none')},
            603: {'grade': 'gold', 'waitress_slots': ('Prinz_Eugen', 'none')},
        })
        # Chao_Ho: +1 capacity, +10% sales
        assert calc.restaurant_capacity[601] == 7
        assert calc.restaurant_quantity[601] == 3
        assert calc.restaurant_sales_bonus[601] == pytest.approx(0.10)
        assert calc.restaurant_enabled[601]
        assert calc.restaurant_grade[601] == 'gold'
        assert calc.restaurant_waitress_slots[601] == ('Chao_Ho', 'none')
        # Prinz_Eugen: +0 capacity, +10% sales
        assert calc.restaurant_capacity[603] == 6
        assert calc.restaurant_sales_bonus[603] == pytest.approx(0.10)


class TestSeasonActivation:
    @pytest.mark.parametrize('season_key', [
        'season_20251106_cn', 'season_20260205_cn', 'season_20260507_cn',
        'season_20260806_cn', 'season_20261105_cn',
    ])
    def test_active_content_comes_from_each_season(
            self, make_calculator, all_unlocked_technology, season_key,
    ):
        season = DIC_ISLAND_SEASON[season_key]
        calc = make_calculator(all_unlocked_technology, season_name=season_key)

        problem = calc._build_production_problem()
        recipe_ids = {
            activity['id'] for activity in problem['activities']
            if activity['kind'] == 'recipe'
        }
        seasonal_recipes = {
            recipe_id for selected in DIC_ISLAND_SEASON.values()
            for recipes in selected['production'].values() for recipe_id in recipes
        }
        expected = {recipe_id for recipes in season['production'].values() for recipe_id in recipes}
        assert recipe_ids.intersection(seasonal_recipes) == expected
        assert {
            gather_id for gather_id, available in calc.wild_gather_available.items()
            if available and gather_id >= 1000
        } == set(season['wild_gather'])
        shop_ids = {
            activity['id'] for activity in problem['activities']
            if activity['kind'] == 'shop'
        }
        assert shop_ids.intersection(DIC_ISLAND_SEASONAL_SHOP_GOODS) == set(season['shop_goods'])

    def test_no_selected_season_disables_seasonal_shop_goods(self, make_calculator):
        calc = make_calculator({})

        problem = calc._build_production_problem()

        assert calc.season is None
        assert not any(
            activity['kind'] == 'shop' and activity['id'] in DIC_ISLAND_SEASONAL_SHOP_GOODS
            for activity in problem['activities']
        )

    @pytest.mark.parametrize(('season_key', 'active_items', 'inactive_items'), [
        ('season_20260806_cn', {4009, 4010}, {4051, 4052}),
        ('season_20261105_cn', {4051, 4052}, {4009, 4010}),
    ])
    def test_restaurant_catalog_only_sells_active_season_dishes(
            self, make_calculator, season_key, active_items, inactive_items,
    ):
        calc = make_calculator(
            {}, season_name=season_key,
            restaurant_settings={601: {'grade': 'gold', 'waitress_slots': ('Chao_Ho', 'none')}},
        )

        problem = calc._build_production_problem()
        menu = {item_id for slot, item_id in problem['sale_entries'] if slot == 601}

        assert active_items <= menu
        assert not inactive_items.intersection(menu)

    @pytest.mark.parametrize(('srv', 'seed_count', 'batch_size', 'limit'), [
        ('cn', 4, 32, 8),
        ('tw', 1, 8, 5),
    ])
    def test_current_server_recipe_definitions_reach_the_model(
            self, make_calculator, all_unlocked_technology, monkeypatch,
            srv, seed_count, batch_size, limit,
    ):
        monkeypatch.setattr(server, 'server', srv)
        permanent_cost = dict(DIC_ISLAND_RECIPE[9900001]['commission_cost'])
        calc = make_calculator(all_unlocked_technology, season_name='season_20260806_cn')

        problem = calc._build_production_problem()
        recipe = next(
            activity for activity in problem['activities']
            if activity['kind'] == 'recipe' and activity['id'] == 9900001
        )

        assert recipe['inputs'] == {4006: seed_count}
        assert recipe['outputs'] == {4005: batch_size}
        assert calc.recipe_data[9900003]['production_limit'] == limit
        assert DIC_ISLAND_RECIPE[9900001]['commission_cost'] == permanent_cost

    def test_server_definitions_apply_without_an_active_season(self, make_calculator, monkeypatch):
        monkeypatch.setattr(server, 'server', 'tw')

        calc = make_calculator({})

        assert calc.season is None
        assert calc.recipe_data[9900001]['commission_cost'] == {4006: 1}
        assert calc.recipe_data[9900001]['commission_product'] == {4005: 8}
        assert calc.recipe_data[601001] == DIC_ISLAND_RECIPE[601001]
