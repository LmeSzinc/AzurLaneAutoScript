"""Quantity selection follows the displayed value when the shop clamps a click."""
from collections import deque

import pytest

import module.base.timer as timer_module
import module.island_handler.shop as shop_module
from module.device.device import Device
from module.exception import GameTooManyClickError
from module.island_handler.shop import IslandShop


STEPS = {
    shop_module.ISLAND_SHOP_BUY_AMOUNT_PLUS_TEN: 10,
    shop_module.ISLAND_SHOP_BUY_AMOUNT_MINUS_TEN: -10,
    shop_module.ISLAND_SHOP_BUY_AMOUNT_PLUS_ONE: 1,
    shop_module.ISLAND_SHOP_BUY_AMOUNT_MINUS_ONE: -1,
}


class QuantityDevice:
    def __init__(self, current, maximum, delay=0, stalled=False):
        self.quantity = current
        self.image = current
        self.maximum = maximum
        self.delay = delay
        self.pending_frames = 0
        self.stalled = stalled
        self.now = 100.0
        self.screenshots = 0
        self.clicks = []
        self.click_record = deque(maxlen=15)
        self.quantities = [current]
        self.readings = []

    def screenshot(self):
        self.screenshots += 1
        assert self.screenshots < 200, 'Quantity selection did not terminate'
        self.now += 0.5
        if self.pending_frames:
            self.pending_frames -= 1
        else:
            self.image = self.quantity

    def click(self, button):
        step = STEPS[button]
        self.clicks.append(step)
        if not self.stalled:
            self.quantity = min(self.maximum, max(1, self.quantity + step))
        self.quantities.append(self.quantity)
        self.pending_frames = self.delay

    def multi_click(self, button, n, interval=(0.2, 0.3)):
        # Device checks the history once for each multi_click batch.
        Device.click_record_add(self, button)
        Device.click_record_check(self)
        for _ in range(n):
            self.click(button)

    click_record_clear = Device.click_record_clear


def make_quantity_shop(monkeypatch, current=1, maximum=999, delay=0, stalled=False):
    device = QuantityDevice(current, maximum, delay=delay, stalled=stalled)
    monkeypatch.setattr(timer_module, 'time', lambda: device.now)

    def read(self, image):
        device.readings.append(image)
        return image

    monkeypatch.setattr(shop_module.Digit, 'ocr', read)
    shop = object.__new__(IslandShop)
    shop.device = device
    return shop, device


@pytest.mark.parametrize(
    'current, target, maximum, clicks, quantities',
    [
        # 1183 coins / 60 per item: the second +10 stops at 19.
        (1, 19, 1183 // 60, [10, 10], [1, 11, 19]),
        # PR 6125 requests 18, one below that same affordable limit.
        (1, 18, 19, [10, 10, -1], [1, 11, 19, 18]),
        (1, 18, 18, [10, 10], [1, 11, 18]),
        (1, 18, 20, [10, 10, -1, -1], [1, 11, 20, 19, 18]),
        (11, 19, 19, [10], [11, 19]),
        (1, 18, 999, [10, 10, -1, -1, -1], [1, 11, 21, 20, 19, 18]),
        # The displayed quantity can already differ from the initial value of 1.
        (25, 18, 999, [-10, 1, 1, 1], [25, 15, 16, 17, 18]),
        (18, 18, 999, [], [18]),
        (1, 5, 999, [1, 1, 1, 1], [1, 2, 3, 4, 5]),
        (1, 7, 7, [10], [1, 7]),
        # A -10 also clamps at the lower boundary of 1.
        (8, 2, 999, [-10, 1], [8, 1, 2]),
    ],
)
def test_quantity_selection_tracks_actual_click_results(
    monkeypatch, current, target, maximum, clicks, quantities
):
    shop, device = make_quantity_shop(monkeypatch, current=current, maximum=maximum)

    shop.island_shop_buy_ensure_amount(target)

    assert device.clicks == clicks
    assert device.quantities == quantities
    assert device.readings[-1] == target


@pytest.mark.parametrize('maximum', range(1, 41))
def test_quantity_selection_reaches_every_valid_quantity(monkeypatch, maximum):
    monkeypatch.setattr(shop_module.logger, 'disabled', True)
    for current in range(1, maximum + 1):
        for target in range(1, maximum + 1):
            shop, device = make_quantity_shop(monkeypatch, current=current, maximum=maximum)

            shop.island_shop_buy_ensure_amount(target)

            case = (current, target, maximum)
            assert device.quantity == target, case
            assert device.readings[-1] == target, case
            assert sum(abs(step) == 1 for step in device.clicks) <= 5, case


def test_quantity_selection_waits_for_a_delayed_frame(monkeypatch):
    shop, device = make_quantity_shop(monkeypatch, maximum=19, delay=1)

    shop.island_shop_buy_ensure_amount(19)

    assert device.clicks == [10, 10]
    assert device.readings[-1] == 19
    assert device.readings.count(1) >= 2


def test_quantity_selection_handles_large_quantity(monkeypatch):
    shop, device = make_quantity_shop(monkeypatch)

    shop.island_shop_buy_ensure_amount(999)

    assert device.clicks == [10] * 100
    assert device.readings[-1] == 999


def test_stalled_quantity_uses_device_guard_without_confirming_purchase(monkeypatch):
    shop, device = make_quantity_shop(monkeypatch, maximum=19, stalled=True)
    confirmations = []
    shop.appear = lambda button, **kwargs: button is shop_module.ISLAND_SHOP_BUY_CHECK
    shop.appear_then_click = lambda button, **kwargs: confirmations.append(button)
    shop.handle_island_additional = lambda: False

    with pytest.raises(GameTooManyClickError):
        shop.island_shop_buy_execute(object(), 19)

    assert device.quantity == 1
    assert device.clicks == [10] * 22
    assert confirmations == []


def test_buy_in_page_rejects_unaffordable_quantity():
    shop = object.__new__(IslandShop)
    shop.island_shop_get_currency = lambda: {1: 1183}
    shop.island_shop_item_ids = [411003]
    purchases = []
    shop.island_shop_buy_execute = lambda button, amount: purchases.append(amount)

    assert shop.island_shop_buy_in_page(411003, 20) is False
    assert purchases == []
