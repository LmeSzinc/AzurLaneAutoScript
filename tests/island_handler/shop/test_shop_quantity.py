"""Regression tests for capped Island Shop purchase quantity selectors."""
import pytest

import module.island_handler.shop as shop_module
from module.island_handler.shop import IslandShop


class FakeDevice:
    def __init__(self, quantity=1, cap=999):
        self.image = object()
        self.quantity = quantity
        self.cap = cap
        self.clicks = []

    def screenshot(self):
        pass

    def multi_click(self, button, n, interval):
        self.clicks.append((button, n))
        if button is shop_module.ISLAND_SHOP_BUY_AMOUNT_PLUS_TEN:
            self.quantity = min(self.cap, self.quantity + 10 * n)
        elif button is shop_module.ISLAND_SHOP_BUY_AMOUNT_PLUS_ONE:
            self.quantity = min(self.cap, self.quantity + n)
        elif button is shop_module.ISLAND_SHOP_BUY_AMOUNT_MINUS_TEN:
            self.quantity = max(1, self.quantity - 10 * n)
        elif button is shop_module.ISLAND_SHOP_BUY_AMOUNT_MINUS_ONE:
            self.quantity = max(1, self.quantity - n)
        else:
            raise AssertionError(f'Unexpected quantity button: {button}')


class FakeTimer:
    def __init__(self, *args, **kwargs):
        pass

    def reached(self):
        return True

    def reset(self):
        pass


class FakeDigit:
    def __init__(self, *args, **kwargs):
        pass

    def ocr(self, image):
        return active_device.quantity


active_device = None


@pytest.fixture
def purchase_shop(monkeypatch):
    global active_device
    active_device = FakeDevice()
    monkeypatch.setattr(shop_module, 'Digit', FakeDigit)
    monkeypatch.setattr(shop_module, 'Timer', FakeTimer)
    shop = object.__new__(IslandShop)
    shop.device = active_device
    shop.loop = lambda timeout=None: (None for _ in range(100))
    yield shop
    active_device = None


def test_purchase_quantity_below_affordable_cap(purchase_shop):
    # Reproduction: 18 seeds requested, affordable maximum is 19.
    purchase_shop.device.cap = 19
    assert purchase_shop.island_shop_buy_ensure_amount(18) is True
    assert purchase_shop.device.quantity == 18
    assert sum(n for _, n in purchase_shop.device.clicks) < 25


def test_purchase_quantity_above_affordable_cap_exits(purchase_shop):
    purchase_shop.device.cap = 19
    assert purchase_shop.island_shop_buy_ensure_amount(20) is False
    assert purchase_shop.device.quantity == 19
    assert len(purchase_shop.device.clicks) < 10


def test_purchase_quantity_can_decrease(purchase_shop):
    purchase_shop.device.quantity = 25
    assert purchase_shop.island_shop_buy_ensure_amount(18) is True
    assert purchase_shop.device.quantity == 18


def test_purchase_quantity_one_needs_no_clicks(purchase_shop):
    assert purchase_shop.island_shop_buy_ensure_amount(1) is True
    assert purchase_shop.device.clicks == []


def test_invalid_purchase_quantity_exits(purchase_shop):
    assert purchase_shop.island_shop_buy_ensure_amount(0) is False
    assert purchase_shop.device.clicks == []
