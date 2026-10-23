import pytest

from module.island.data import DIC_ISLAND_ACTIVITY


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

    def test_activity_list_enables_activity_content(self, make_calculator):
        recipe_activity_id, recipe_ids = next(
            (activity_id, data['config_data'])
            for activity_id, data in DIC_ISLAND_ACTIVITY.items()
            if data['type'] == 5004 and data['config_data']
        )
        gather_activity_id, gather_ids = next(
            (activity_id, data['config_data'])
            for activity_id, data in DIC_ISLAND_ACTIVITY.items()
            if data['type'] == 5003 and data['config_data']
        )
        calc = make_calculator({}, activity_list=[recipe_activity_id, gather_activity_id])
        for recipe_id in recipe_ids:
            assert calc.recipe_available[recipe_id], recipe_id
        for gather_id in gather_ids:
            assert calc.wild_gather_available[gather_id], gather_id
        # Without the activity list they stay unavailable, unless the recipe
        # is also attached to an available slot's activity_formula
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
