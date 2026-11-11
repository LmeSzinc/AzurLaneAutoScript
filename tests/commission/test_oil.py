import pytest

from module.commission.oil import (
    BUY_FOOD,
    NAVAL_CURRY_OIL_COST,
    OIL_CAP,
    OIL_OVERFLOW_THRESHOLD,
    OIL_REFUSED_MIN,
    RECEIVE,
    SKIP,
    food_to_buy,
    is_oil_overflow,
    is_refused_by_oil,
    oil_overflow_action,
)


def test_threshold_is_below_cap():
    assert 0 < OIL_REFUSED_MIN < OIL_OVERFLOW_THRESHOLD < OIL_CAP


@pytest.mark.parametrize('oil, expected', [
    (0, True),  # unknown oil, trust the game
    (-1, True),
    (100, False),
    (OIL_REFUSED_MIN - 1, False),
    (OIL_REFUSED_MIN, True),
    (24994, True),
    (OIL_CAP, True),
])
def test_is_refused_by_oil(oil, expected):
    assert is_refused_by_oil(oil) is expected


@pytest.mark.parametrize('oil, expected', [
    (0, False),  # unknown oil, OCR failed
    (17272, False),
    (OIL_OVERFLOW_THRESHOLD - 1, False),
    (OIL_OVERFLOW_THRESHOLD, True),
    (24994, True),  # refused in game at this amount
    (OIL_CAP, True),
    (26000, True),
])
def test_is_oil_overflow(oil, expected):
    assert is_oil_overflow(oil) is expected


@pytest.mark.parametrize('oil, buy_food, expected', [
    (0, True, RECEIVE),
    (0, False, RECEIVE),
    (20000, True, RECEIVE),
    (20000, False, RECEIVE),
    (OIL_CAP, True, BUY_FOOD),
    (OIL_CAP, False, SKIP),
    (24994, True, BUY_FOOD),
    (24994, False, SKIP),
])
def test_oil_overflow_action(oil, buy_food, expected):
    assert oil_overflow_action(oil, buy_food=buy_food) == expected


@pytest.mark.parametrize('oil_to_spend, expected', [
    (4000, 80),  # default
    (4020, 80),  # round down to whole servings
    (500, 10),
    (NAVAL_CURRY_OIL_COST, 1),
    (10, 1),  # at least one serving
    (0, 1),
    (-100, 1),
    ('4000', 80),
    (None, 1),
    ('abc', 1),
])
def test_food_to_buy(oil_to_spend, expected):
    assert food_to_buy(oil_to_spend) == expected
