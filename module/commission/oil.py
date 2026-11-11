"""
Oil cap handling for commission rewards.

Commission rewards can't be received while oil is at the cap. The game refuses
them as soon as the oil in a reward would push the current oil over the cap,
which is why players see the refusal at 24994 oil too.
"""

# Oil cap from commissions and missions
OIL_CAP = 25000
# Commission rewards carry up to about 1000 oil each,
# so start making room before reaching the exact cap.
OIL_OVERFLOW_THRESHOLD = 24000
# One claim of commission rewards brings far less oil than this,
# so the cap can't be the reason rewards were refused when oil is lower.
OIL_REFUSED_MIN = OIL_CAP - 5000
# Naval Curry, the 5000 supplies food in dorm, costs 50 oil
NAVAL_CURRY_OIL_COST = 50
# Minutes to wait before checking again when rewards are left unclaimed
OIL_OVERFLOW_RECHECK = 60

RECEIVE = 'receive'
BUY_FOOD = 'buy_food'
SKIP = 'skip'


def is_oil_overflow(oil):
    """
    Args:
        oil (int): Current oil, 0 if unknown.

    Returns:
        bool: If commission rewards may be refused because of the oil cap.
    """
    return oil >= OIL_OVERFLOW_THRESHOLD


def is_refused_by_oil(oil):
    """
    Args:
        oil (int): Current oil, 0 if unknown.

    Returns:
        bool: If the oil cap can explain why the game refused commission rewards.
            Unknown oil counts as yes.
    """
    return oil <= 0 or oil >= OIL_REFUSED_MIN


def oil_overflow_action(oil, buy_food):
    """
    Args:
        oil (int): Current oil, 0 if unknown.
        buy_food (bool): Commission_OilOverflowBuyFood

    Returns:
        str: RECEIVE to receive rewards as usual,
            BUY_FOOD to spend oil on food then receive,
            SKIP to leave rewards unclaimed and check again later.
    """
    if not is_oil_overflow(oil):
        return RECEIVE
    if buy_food:
        return BUY_FOOD
    return SKIP


def food_to_buy(oil_to_spend):
    """
    Args:
        oil_to_spend (int): Commission_OilOverflowAmount

    Returns:
        int: Amount of Naval Curry to buy, at least 1.
    """
    try:
        oil_to_spend = int(oil_to_spend)
    except (TypeError, ValueError):
        oil_to_spend = 0
    return max(oil_to_spend // NAVAL_CURRY_OIL_COST, 1)
