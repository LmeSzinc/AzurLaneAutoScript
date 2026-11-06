"""Unit tests for the Island Shop quantity selector (no ALAS emulator required)."""

from module.island_handler.shop_quantity import ensure_purchase_quantity


class FakeCounter:
    """Simulate the in-game quantity selector and a maximum affordable amount."""

    def __init__(self, quantity=1, cap=999):
        self.quantity = quantity
        self.cap = cap
        self.clicks = []

    def read(self):
        return self.quantity

    def press(self, button, count):
        self.clicks.append((button, count))
        direction = 1 if button.startswith('plus') else -1
        size = 10 if button.endswith('ten') else 1
        self.quantity = max(1, min(self.cap, self.quantity + direction * size * count))


def test_request_18_with_affordable_cap_19():
    # Original production failure: 1183 coins, 60 per seed, 18 requested.
    counter = FakeCounter(cap=19)
    assert ensure_purchase_quantity(18, counter.read, counter.press)
    assert counter.quantity == 18
    assert counter.clicks[0] == ('plus_ten', 1)
    assert len(counter.clicks) <= 5


def test_unreachable_request_stops_without_click_loop():
    counter = FakeCounter(cap=19)
    assert not ensure_purchase_quantity(20, counter.read, counter.press)
    assert counter.quantity == 19
    assert len(counter.clicks) <= 6


def test_selector_stuck_at_initial_quantity():
    counter = FakeCounter(cap=1)
    assert not ensure_purchase_quantity(18, counter.read, counter.press)
    assert counter.quantity == 1
    assert len(counter.clicks) == 1


def test_can_decrease_existing_quantity():
    counter = FakeCounter(quantity=25)
    assert ensure_purchase_quantity(18, counter.read, counter.press)
    assert counter.quantity == 18
    assert counter.clicks[0] == ('minus_one', 3)


def test_large_increment_and_exact_quantity():
    counter = FakeCounter()
    assert ensure_purchase_quantity(31, counter.read, counter.press)
    assert counter.quantity == 31
    assert counter.clicks == [('plus_ten', 3)]


def test_one_item_needs_no_clicks():
    counter = FakeCounter()
    assert ensure_purchase_quantity(1, counter.read, counter.press)
    assert counter.clicks == []


def test_invalid_target_does_not_click():
    counter = FakeCounter()
    assert not ensure_purchase_quantity(0, counter.read, counter.press)
    assert counter.clicks == []


def test_invalid_ocr_amount_does_not_click():
    counter = FakeCounter(quantity=0)
    assert not ensure_purchase_quantity(18, counter.read, counter.press)
    assert counter.clicks == []
