from datetime import datetime

import pytest

from dev_tools import island_extractor
from dev_tools.island_extractor import get_slot_ingredient_sources, seasons_for_period
from module.island import data, season_data
from module.island.data import (
    DIC_ISLAND_EXCHANGE_RECIPE,
    DIC_ISLAND_RECIPE,
    DIC_ISLAND_SHOP_RECIPE,
    DIC_ISLAND_SLOT,
)


def recipe(cost=(), product=(), secondary=()):
    return {
        'commission_cost': dict(cost),
        'commission_product': dict(product),
        'second_product_display': dict(secondary),
    }


def conversion(consumes, products):
    return {
        'resource_consume': dict(consumes),
        'items': dict(products),
    }


def test_consecutive_extractors_load_cn_first(tmp_path, monkeypatch):
    for server in ('CN', 'EN', 'JP', 'TW'):
        (tmp_path / server).mkdir()

    requests = []

    def record_load(loader, path, keyword=None):
        requests.append((loader, loader.server, path))
        if path == 'sharecfg/island_shop_template.lua':
            # These shops are required by the extractor's order corrections.
            return {
                shop_id: {
                    'tag_type': 1, 'order': 0, 'top_resource': {},
                    'goods_id': {}, 'tag_icon': {0: 'Shop'},
                }
                for shop_id in (10020, 10021, 10112, 10113)
            }
        return {}

    loader = island_extractor.LuaLoader(str(tmp_path), server='CN')
    monkeypatch.setattr(island_extractor, 'LOADER', loader, raising=False)
    monkeypatch.setattr(island_extractor.LuaLoader, 'load', record_load)

    # Follow main's order, keeping the same loader between extractors.
    # Mining and logging are omitted because they do not load Lua data.
    for extractor in (
        island_extractor.IslandItemExtractor,
        island_extractor.IslandRecipeExtractor,
        island_extractor.IslandProductionExtractor,
        island_extractor.IslandShopItemExtractor,
        island_extractor.IslandExchangeRecipeExtractor,
        island_extractor.IslandActivityExtractor,
        island_extractor.IslandWildGatherExtractor,
        island_extractor.IslandSeasonExtractor,
        island_extractor.IslandSeasonRequestExtractor,
        island_extractor.IslandShopExtractor,
        island_extractor.IslandTaskExtractor,
        island_extractor.IslandRestaurantExtractor,
        island_extractor.IslandTechnologyExtractor,
        island_extractor.IslandProductionPlaceExtractor,
    ):
        requests.clear()
        extractor()
        assert requests[0][1] == 'CN', (extractor.__name__, requests[0][2])
        assert all(
            server == 'CN' for request_loader, server, _ in requests if request_loader is loader
        ), extractor.__name__
        assert loader.server == 'CN', extractor.__name__


def test_sources_include_primary_secondary_and_activity_outputs():
    slots = {
        1: {'formula': [101]},
        2: {'formula': [201]},
        3: {'formula': [301]},
        4: {'formula': [401]},
    }
    recipes = {
        101: recipe(product={20: 1}, secondary={30: 1}),
        102: recipe(product={40: 1}),
        201: recipe(cost={20: 1}, product={50: 1}),
        301: recipe(cost={30: 1}, product={51: 1}),
        401: recipe(cost={40: 1}, product={52: 1}),
    }

    sources = get_slot_ingredient_sources(slots, recipes, [], {1: [102]})

    assert sources[2] == [1]
    assert sources[3] == [1]
    assert sources[4] == [1]
    assert get_slot_ingredient_sources(slots, recipes, [])[4] == []
    assert slots[1] == {'formula': [101]}


def test_conversions_chain_but_production_outputs_require_their_slot():
    slots = {
        1: {'formula': [101]},
        2: {'formula': [201]},
        3: {'formula': [301]},
        4: {'formula': [401]},
        5: {'formula': [501]},
    }
    recipes = {
        101: recipe(product={10: 1}),
        201: recipe(cost={10: 1}, product={20: 1}),
        301: recipe(cost={20: 1}, product={30: 1}),
        401: recipe(product={100: 1}),
        501: recipe(cost={300: 1}, product={500: 1}),
    }
    conversions = [
        conversion({100: 1}, {200: 1}),
        conversion({200: 1}, {300: 1}),
    ]

    sources = get_slot_ingredient_sources(slots, recipes, conversions)

    assert sources[2] == [1]
    assert sources[3] == [2]
    assert 1 not in sources[3]
    assert sources[5] == [4]
    assert 1 not in sources[5]


def test_current_data_keeps_secondary_and_conversion_dependencies():
    conversions = list(DIC_ISLAND_SHOP_RECIPE.values()) + list(DIC_ISLAND_EXCHANGE_RECIPE.values())
    sources = get_slot_ingredient_sources(DIC_ISLAND_SLOT, DIC_ISLAND_RECIPE, conversions)

    # Chicken and leather are secondary outputs of the two ranch recipes.
    assert 9031 in sources[9061]  # eggs provide chicken for restaurant 9061
    assert 9033 in sources[9207]  # milk provides leather for industry 9207

    # Crops can be converted to animal feed and flour before dispatch.
    assert 9001 in sources[9031]  # wheat -> chicken feed
    assert 9001 in sources[9081]  # wheat -> flour

    # Fishery 9211 can be exchanged for the meat consumed by restaurant 9061.
    assert 9211 in sources[9061]

    # Isolate the exchange path: recipe 601006 needs saltwater meat and
    # wheatgrass; fishery 9211 supplies neither directly.
    exchange_only_sources = get_slot_ingredient_sources(
        {
            9211: DIC_ISLAND_SLOT[9211],
            9999: {'formula': [601006]},
        },
        DIC_ISLAND_RECIPE,
        list(DIC_ISLAND_EXCHANGE_RECIPE.values()),
    )
    assert exchange_only_sources[9999] == [9211]

    # A production output from 9207 is not an instant input to 9071.
    assert 9207 not in sources[9071]


def lua_time(text):
    value = datetime.fromisoformat(text)
    return {
        0: dict(enumerate((value.year, value.month, value.day))),
        1: dict(enumerate((value.hour, value.minute, value.second))),
    }


def lua_period(start, end):
    return {0: lua_time(start), 1: lua_time(end)}


@pytest.fixture
def season_schedule():
    boundaries = (
        ('2025-09-29 00:00:00', '2026-02-05 12:00:00'),
        ('2026-02-05 12:00:01', '2026-05-07 12:00:00'),
        ('2026-05-07 12:00:01', '2026-08-06 12:00:00'),
    )
    return {
        f'season_{index}': {'start_time': {'cn': start}, 'end_time': {'cn': end}}
        for index, (start, end) in enumerate(boundaries, start=1)
    }


@pytest.mark.parametrize('start_hour', ['00:00:00', '12:00:01'])
def test_period_transition_day_belongs_to_new_season(season_schedule, start_hour):
    period = lua_period(f'2026-02-05 {start_hour}', '2026-05-07 12:00:00')
    assert seasons_for_period(period, season_schedule) == ['season_2']


def test_period_can_start_before_first_season_or_span_multiple_seasons(season_schedule):
    first_shop = lua_period('2025-09-25 00:00:00', '2026-02-05 12:00:00')
    assert seasons_for_period(first_shop, season_schedule) == ['season_1']
    several = lua_period('2026-02-05 00:00:00', '2026-08-06 12:00:00')
    assert seasons_for_period(several, season_schedule) == ['season_2', 'season_3']


def test_period_always_stop_and_unpublished_server(season_schedule):
    assert seasons_for_period('always', season_schedule) == list(season_schedule)
    assert seasons_for_period('stop', season_schedule) == []
    assert seasons_for_period(None, season_schedule) == []
    assert seasons_for_period(
        lua_period('2026-02-05 00:00:00', '2026-05-07 12:00:00'), season_schedule, server='tw',
    ) == []


def test_generated_permanent_catalog_has_no_season_activation_fields():
    for constant in ('DIC_ISLAND_ACTIVITY', 'DIC_ISLAND_SEASON', 'DIC_ISLAND_SEASON_ORDER'):
        assert not hasattr(data, constant)
    for table in (data.DIC_ISLAND_SLOT, data.DIC_ISLAND_WILD_GATHER,
                  data.DIC_ISLAND_SHOP_RECIPE, data.DIC_ISLAND_TASK):
        for entry in table.values():
            assert not {'activity_formula', 'activity_id', 'start_time', 'end_time'}.intersection(entry)
    # Seasonal recipes remain permanent definitions, including older specialties.
    assert {9900001, 9900003, 9900025, 9900032} <= set(data.DIC_ISLAND_RECIPE)


def test_generated_seasons_have_four_activities_and_matching_current_content():
    expected_dates = ('20251106', '20260205', '20260507', '20260806', '20261105')
    assert list(season_data.DIC_ISLAND_SEASON) == [f'season_{date}_cn' for date in expected_dates]
    for date in expected_dates:
        season = season_data.DIC_ISLAND_SEASON[f'season_{date}_cn']
        assert not {'start_time', 'end_time', 'season_order'}.intersection(season)
        assert [season_data.DIC_ISLAND_ACTIVITY[index]['type'] for index in season['activity']] == [
            5001, 5002, 5003, 5004,
        ]
        order_activity, gather_activity, recipe_activity = season['activity'][1:]
        orders = [
            season_data.DIC_ISLAND_SEASON_ORDER[index]
            for index in season_data.DIC_ISLAND_ACTIVITY[order_activity]['config_data']
        ]
        assert all(order['group_id'] == order_activity for order in orders)
        assert set(season['wild_gather']) == set(season_data.DIC_ISLAND_ACTIVITY[gather_activity]['config_data'])
        assert {index for formulas in season['production'].values() for index in formulas} == set(
            season_data.DIC_ISLAND_ACTIVITY[recipe_activity]['config_data']
        )
        assert set(season['task_list']) <= set(season['tasks']) <= set(data.DIC_ISLAND_TASK)


def test_activity_window_matches_season_despite_maintenance_time(season_schedule):
    assert island_extractor.get_season_namespace(
        '2026-02-05 00:00:00', '2026-05-07 12:00:00', season_schedule,
    ) == 'season_2'


def test_generated_catalog_uses_current_values_and_tw_recipe_differences():
    first = season_data.DIC_ISLAND_SEASON['season_20251106_cn']
    assert data.DIC_ISLAND_RECIPE[9900001]['commission_cost'] == {4006: 4}
    assert data.DIC_ISLAND_RECIPE[9900001]['commission_product'] == {4005: 32}
    assert data.DIC_ISLAND_RECIPE[601001]['workload'] == 24000
    assert data.DIC_ISLAND_RECIPE[601001]['production_limit'] == 12
    tw_recipes = season_data.DIC_ISLAND_SERVER_OVERRIDES['tw']['recipe_overrides']
    assert tw_recipes[9900001]['commission_cost'] == {4006: 1}
    assert tw_recipes[9900001]['commission_product'] == {4005: 8}
    assert 601001 not in tw_recipes
    assert [key for key, season in season_data.DIC_ISLAND_SEASON.items() if 411023 in season['shop_goods']] == [
        'season_20260806_cn',
    ]
    assert first['shop_goods'] == []
    assert [len(season['tasks']) for season in season_data.DIC_ISLAND_SEASON.values()] == [49, 62, 56, 49, 49]
