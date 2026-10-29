from dev_tools.island_extractor import get_slot_ingredient_sources
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


def test_sources_include_primary_secondary_and_activity_outputs():
    slots = {
        1: {'formula': [101], 'activity_formula': [102]},
        2: {'formula': [201], 'activity_formula': []},
        3: {'formula': [301], 'activity_formula': []},
        4: {'formula': [401], 'activity_formula': []},
    }
    recipes = {
        101: recipe(product={20: 1}, secondary={30: 1}),
        102: recipe(product={40: 1}),
        201: recipe(cost={20: 1}, product={50: 1}),
        301: recipe(cost={30: 1}, product={51: 1}),
        401: recipe(cost={40: 1}, product={52: 1}),
    }

    sources = get_slot_ingredient_sources(slots, recipes, [])

    assert sources[2] == [1]
    assert sources[3] == [1]
    assert sources[4] == [1]


def test_conversions_chain_but_production_outputs_require_their_slot():
    slots = {
        1: {'formula': [101], 'activity_formula': []},
        2: {'formula': [201], 'activity_formula': []},
        3: {'formula': [301], 'activity_formula': []},
        4: {'formula': [401], 'activity_formula': []},
        5: {'formula': [501], 'activity_formula': []},
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
            9999: {'formula': [601006], 'activity_formula': []},
        },
        DIC_ISLAND_RECIPE,
        list(DIC_ISLAND_EXCHANGE_RECIPE.values()),
    )
    assert exchange_only_sources[9999] == [9211]

    # A production output from 9207 is not an instant input to 9071.
    assert 9207 not in sources[9071]
