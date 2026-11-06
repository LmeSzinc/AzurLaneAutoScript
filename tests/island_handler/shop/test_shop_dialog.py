"""Isolated tests of the actual Island Shop dialog control flow.

Extract only the target methods from shop.py via Python's AST so these tests
exercise production logic without importing the ALAS emulator and OCR stack.
"""
import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from module.island_handler.shop_quantity import close_purchase_dialog


SOURCE = Path(__file__).resolve().parents[3] / 'module/island_handler/shop.py'


class RequestHumanTakeover(Exception):
    pass


class FakeLogger:
    def error(self, message):
        pass


def shop_method(name):
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'IslandShop')
    fn = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
    env = {
        'RequestHumanTakeover': RequestHumanTakeover,
        'close_purchase_dialog': close_purchase_dialog,
        'ISLAND_SHOP_BUY_CHECK': 'dialog',
        'ISLAND_SHOP_BUY_CONFIRM': 'confirm',
        'BACK_ARROW_WHITE': 'back',
        'logger': FakeLogger(),
        'DIC_ISLAND_SHOP_RECIPE': {123: {'resource_consume': {1: 60}}},
        'item_name_with_id': str,
    }
    code = compile(ast.Module(body=[fn], type_ignores=[]), str(SOURCE), 'exec')
    exec(code, env)
    return env[name]


class FakeDevice:
    def __init__(self, shop):
        self.shop = shop
        self.clicks = []
        self.screenshots = 0

    def click(self, button):
        self.clicks.append(button)
        if button == 'back' and self.shop.back_works:
            self.shop.dialog_open = False

    def screenshot(self):
        self.screenshots += 1

    def sleep(self, duration):
        pass


class FakeShop:
    def __init__(self, selector_ok):
        self.dialog_open = True
        self.back_visible = True
        self.back_works = True
        self.selector_ok = selector_ok
        self.confirm_enabled = True
        self.confirm_closes = True
        self.confirm_clicks = 0
        self.device = FakeDevice(self)

    def loop(self, timeout=None):
        # Bounded, so an unverified purchase cannot appear to complete.
        for _ in range(8):
            yield None

    def appear(self, button, offset=None, interval=None):
        if button == 'dialog':
            return self.dialog_open
        if button == 'back':
            return self.back_visible
        return False

    def appear_then_click(self, button, offset=None, interval=None):
        if button == 'confirm' and self.dialog_open and self.confirm_enabled:
            self.confirm_clicks += 1
            if self.confirm_closes:
                self.dialog_open = False
            return True
        return False

    def island_shop_buy_ensure_amount(self, amount):
        return self.selector_ok

    def handle_island_additional(self):
        return False

    def interval_reset(self, button):
        pass


def test_failed_quantity_closes_dialog_without_confirming():
    shop = FakeShop(selector_ok=False)
    assert shop_method('island_shop_buy_execute')(shop, 'item', 20) is False
    assert shop.device.clicks == ['back']
    assert shop.confirm_clicks == 0
    assert not shop.dialog_open


def test_failed_quantity_refuses_to_continue_if_back_does_not_work():
    shop = FakeShop(selector_ok=False)
    shop.back_works = False
    with pytest.raises(RequestHumanTakeover, match='dismiss'):
        shop_method('island_shop_buy_execute')(shop, 'item', 20)
    assert shop.dialog_open
    assert shop.confirm_clicks == 0
    assert len(shop.device.clicks) == 4


def test_failed_quantity_refuses_to_continue_if_back_is_not_visible():
    shop = FakeShop(selector_ok=False)
    shop.back_visible = False
    with pytest.raises(RequestHumanTakeover, match='dismiss'):
        shop_method('island_shop_buy_execute')(shop, 'item', 20)
    assert shop.dialog_open
    assert shop.confirm_clicks == 0
    assert shop.device.clicks == []


def test_success_requires_confirmation_and_closed_dialog():
    shop = FakeShop(selector_ok=True)
    assert shop_method('island_shop_buy_execute')(shop, 'item', 18) is True
    assert shop.confirm_clicks == 1
    assert not shop.dialog_open


def test_visible_back_arrow_cannot_fake_success_without_confirmation():
    shop = FakeShop(selector_ok=True)
    shop.confirm_enabled = False
    with pytest.raises(RequestHumanTakeover, match='completion'):
        shop_method('island_shop_buy_execute')(shop, 'item', 18)
    assert shop.confirm_clicks == 0
    assert shop.dialog_open


def test_confirmation_click_without_dialog_closing_is_not_success():
    shop = FakeShop(selector_ok=True)
    shop.confirm_closes = False
    with pytest.raises(RequestHumanTakeover, match='completion'):
        shop_method('island_shop_buy_execute')(shop, 'item', 18)
    assert shop.confirm_clicks > 0
    assert shop.dialog_open


def test_failed_purchase_result_propagates_to_shopping_routine():
    shop = SimpleNamespace(
        island_shop_get_currency=lambda: {1: 2000},
        get_protected_items=lambda ids: {},
        island_shop_item_ids=[123],
        _island_shop_item_grid=SimpleNamespace(buttons=['item']),
        island_shop_buy_execute=lambda button, amount: False,
    )
    assert shop_method('island_shop_buy_in_page')(shop, 123, 18) is False


def test_successful_purchase_result_propagates_to_shopping_routine():
    shop = SimpleNamespace(
        island_shop_get_currency=lambda: {1: 2000},
        get_protected_items=lambda ids: {},
        island_shop_item_ids=[123],
        _island_shop_item_grid=SimpleNamespace(buttons=['item']),
        island_shop_buy_execute=lambda button, amount: True,
    )
    assert shop_method('island_shop_buy_in_page')(shop, 123, 18) is True
