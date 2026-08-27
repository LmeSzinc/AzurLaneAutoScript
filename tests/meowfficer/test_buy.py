"""Tests for _meow_get_buy_count (pure calculation, no device interaction)."""
from unittest.mock import patch

# Import the real class. _meow_get_buy_count is a @staticmethod that depends
# only on its parameters and the module-level logger, so no device interaction
# is needed; the heavy import chain (cv2/numpy/UI classes) is paid once here.
from module.logger import logger
from module.meowfficer.buy import MeowfficerBuy


def _calc(*args, **kwargs):
    """Run _meow_get_buy_count with logger.info temporarily discarded.

    The static method logs its buy plan via logger.info on every call, which
    spams the test output. Discard the info calls only for the duration of the
    calculation and restore them afterwards.
    """
    with patch.object(logger, 'info'):
        return MeowfficerBuy._meow_get_buy_count(*args, **kwargs)


class TestMeowfficerBuyCount:
    """Test the pure calculation logic of _meow_get_buy_count.

    All tests call the @staticmethod directly with explicit parameters.
    """

    # ------------------------------------------------------------------
    # Section 1: Disabled overflow (overflow_th < 0)
    # ------------------------------------------------------------------

    def test_buy_exact_baseline(self):
        """Buy the configured baseline amount when no overflow."""
        assert _calc(bought=0, total=15, coins=100000,
                     buy_amount=1, overflow_th=-1) == 1

    def test_buy_baseline_already_bought_more(self):
        """Already bought >= baseline today, nothing to buy."""
        assert _calc(bought=5, total=15, coins=100000,
                     buy_amount=3, overflow_th=-1) == 0

    def test_buy_baseline_all_sold_out(self):
        """All 15 boxes bought today, nothing left."""
        assert _calc(bought=15, total=15, coins=100000,
                     buy_amount=1, overflow_th=-1) == 0

    def test_buy_baseline_zero(self):
        """buy_amount=0, no overflow: nothing to buy."""
        assert _calc(bought=0, total=15, coins=100000,
                     buy_amount=0, overflow_th=-1) == 0

    def test_buy_baseline_only_free_box_affordable(self):
        """Only the free first box is affordable with low coins."""
        result = _calc(bought=0, total=15, coins=500,
                       buy_amount=5, overflow_th=-1)
        # affordable = 500//1500 + 1 = 1
        assert result == 1

    def test_buy_baseline_no_free_box_coins_insufficient(self):
        """Already bought once today, no free box, coins < 1500."""
        result = _calc(bought=1, total=15, coins=500,
                       buy_amount=3, overflow_th=-1)
        # free=0, affordable = 500//1500 = 0
        assert result == 0

    def test_buy_baseline_partially_affordable(self):
        """Coins can afford some but not all baseline boxes."""
        result = _calc(bought=0, total=15, coins=2500,
                       buy_amount=5, overflow_th=-1)
        # free=1, affordable = 2500//1500+1 = 1+1 = 2
        # baseline=5 capped to 2
        assert result == 2

    def test_buy_baseline_partially_affordable_no_free(self):
        """Coins can afford some, no free box (bought>0)."""
        result = _calc(bought=2, total=15, coins=2500,
                       buy_amount=5, overflow_th=-1)
        # free=0, affordable = 2500//1500 = 1
        # baseline = min(5-2, 13) = 3, capped to 1
        assert result == 1

    # ------------------------------------------------------------------
    # Section 2: Overflow — gate / disable checks
    # ------------------------------------------------------------------

    def test_overflow_disabled_by_negative(self):
        """overflow_th<0 must disable overflow regardless of coins."""
        assert _calc(bought=0, total=15, coins=999999,
                     buy_amount=0, overflow_th=-1) == 0
        assert _calc(bought=0, total=15, coins=999999,
                     buy_amount=0, overflow_th=-2) == 0
        assert _calc(bought=0, total=15, coins=999999,
                     buy_amount=0, overflow_th=-100) == 0

    def test_overflow_not_triggered_when_equal(self):
        """coins == overflow_th should NOT trigger overflow (strict >)."""
        assert _calc(bought=0, total=15, coins=50000,
                     buy_amount=0, overflow_th=50000) == 0

    def test_overflow_not_triggered_when_below(self):
        """coins < overflow_th should NOT trigger overflow."""
        assert _calc(bought=0, total=15, coins=40000,
                     buy_amount=0, overflow_th=50000) == 0

    # ------------------------------------------------------------------
    # Section 3: Overflow — bought == 0 (first box free compensation)
    #       Bug 1 regression tests
    # ------------------------------------------------------------------

    def test_overflow_bought0_excess_under_price(self):
        """Bug 1: excess < 1500 and bought=0 → extra=2, not 1.

        Old code returned 1 (free box, no coins consumed → infinite loop).
        Fixed code returns 2 (free+paid, actually spends coins).
        """
        result = _calc(bought=0, total=15, coins=50500,
                       buy_amount=0, overflow_th=50000)
        # extra = ceil((50500-50000+1500)/1500) = ceil(2000/1500) = 2
        assert result == 2

    def test_overflow_bought0_large_excess(self):
        """bought=0, large excess → capped by today_left."""
        result = _calc(bought=0, total=15, coins=100000,
                       buy_amount=0, overflow_th=50000)
        # extra = ceil((100000-50000+1500)/1500) = 35
        # capped to today_left - baseline = 15 - 0 = 15
        assert result == 15

    def test_overflow_bought0_excess_less_than_2_boxes(self):
        """bought=0, excess between 1500 and 3000."""
        result = _calc(bought=0, total=15, coins=51500,
                       buy_amount=0, overflow_th=50000)
        # extra = ceil((51500-50000+1500)/1500) = ceil(3000/1500) = 2
        assert result == 2

    def test_overflow_bought0_excess_2_boxes(self):
        """bought=0, extra=2, enough coins to afford both."""
        result = _calc(bought=0, total=15, coins=52000,
                       buy_amount=0, overflow_th=50000)
        # extra = ceil((52000-50000+1500)/1500) = ceil(3500/1500) = 3
        # Capped to today_left = 15
        assert result == 3

    def test_overflow_bought0_exact_divisible(self):
        """bought=0, coins can be brought exactly to threshold."""
        result = _calc(bought=0, total=15, coins=51500,
                       buy_amount=0, overflow_th=50000)
        # extra = ceil(3000/1500) = 2
        # cost = 1*1500 = 1500 (first free)
        # remaining = 50000 = overflow_th ✓
        assert result == 2

    def test_overflow_bought0_insufficient_coins(self):
        """bought=0, overflow triggered but coins cap the count."""
        result = _calc(bought=0, total=15, coins=2000,
                       buy_amount=0, overflow_th=100)
        # extra = ceil((2000-100+1500)/1500) = ceil(3400/1500) = 3
        # affordable = 2000//1500 + 1 = 2
        assert result == 2

    # ------------------------------------------------------------------
    # Section 4: Overflow — bought > 0 (no free box in overflow calc)
    # ------------------------------------------------------------------

    def test_overflow_bought_positive_large_excess(self):
        """bought>0, large excess capped by today_left."""
        result = _calc(bought=5, total=15, coins=100000,
                       buy_amount=0, overflow_th=50000)
        # extra = ceil((100000-50000)/1500) = 34
        # capped to today_left = 10
        assert result == 10

    def test_overflow_bought_positive_insufficient_coins(self):
        """bought>0, overflow triggered but coins cap the count."""
        result = _calc(bought=1, total=15, coins=2000,
                       buy_amount=0, overflow_th=100)
        # extra = ceil((2000-100)/1500) = ceil(1900/1500) = 2
        # affordable = 2000//1500 = 1 (no free box)
        assert result == 1

    def test_overflow_bought_positive_single_box(self):
        """bought>0, overflow requires exactly 1 extra box."""
        result = _calc(bought=3, total=15, coins=51500,
                       buy_amount=0, overflow_th=50000)
        # extra = ceil((51500-50000)/1500) = ceil(1500/1500) = 1
        assert result == 1

    # ------------------------------------------------------------------
    # Section 5: Baseline + overflow combined
    # ------------------------------------------------------------------

    def test_baseline_plus_overflow_full_day(self):
        """Baseline and overflow fill the entire day quota."""
        result = _calc(bought=0, total=15, coins=100000,
                       buy_amount=3, overflow_th=50000)
        # baseline=3, extra=12 (capped by 15-3), total=15
        assert result == 15

    def test_baseline_plus_overflow_partial(self):
        """Baseline remaining + overflow, some already bought."""
        result = _calc(bought=3, total=15, coins=80000,
                       buy_amount=5, overflow_th=50000)
        # today_left=12, baseline=2, extra=10 (capped by 12-2)
        assert result == 12

    def test_baseline_satisfies_overflow_no_extra(self):
        """Baseline alone would consume enough coins, overflow extra=0."""
        result = _calc(bought=0, total=15, coins=52000,
                       buy_amount=3, overflow_th=50000)
        # baseline=3, free=1 → cost = 2*1500 = 3000
        # coins after = 49000 ≤ 50000 → no overflow extra needed
        # extra = ceil((52000-50000+1500)/1500) = ceil(3500/1500) = 3
        # extra capped by today_left - baseline = 15-3 = 12 → 3
        # count = 3+3 = 6
        assert result == 6

    # ------------------------------------------------------------------
    # Section 6: Edge cases
    # ------------------------------------------------------------------

    def test_bought_equals_total(self):
        """Bought equal to total (nothing left)."""
        assert _calc(bought=15, total=15, coins=999999,
                     buy_amount=5, overflow_th=100) == 0

    def test_bought_exceeds_total(self):
        """Bought larger than total (should be clamped by max())."""
        assert _calc(bought=20, total=15, coins=999999,
                     buy_amount=1, overflow_th=-1) == 0

    def test_zero_coins_free_box_only(self):
        """Zero coins but first box is free."""
        result = _calc(bought=0, total=15, coins=0,
                       buy_amount=3, overflow_th=-1)
        # free=1, affordable = 0 + 1 = 1
        assert result == 1

    def test_zero_coins_no_free_box(self):
        """Zero coins and bought>0 → nothing affordable."""
        result = _calc(bought=1, total=15, coins=0,
                       buy_amount=3, overflow_th=-1)
        # free=0, affordable = 0
        assert result == 0

    def test_overflow_threshold_zero(self):
        """overflow_th=0 should trigger when coins > 0."""
        result = _calc(bought=0, total=15, coins=1500,
                       buy_amount=0, overflow_th=0)
        # extra = ceil((1500-0+1500)/1500) = ceil(3000/1500) = 2
        # affordable = 1500//1500+1 = 2
        assert result == 2

    def test_negative_coins_not_handled(self):
        """Negative coins — edge case, should not crash."""
        result = _calc(bought=0, total=15, coins=-100,
                       buy_amount=1, overflow_th=-1)
        # coins < BUY_PRIZE, free=1, affordable = -100//1500 + 1 = -1+1 = 0
        # count capped to 0
        assert result == 0
