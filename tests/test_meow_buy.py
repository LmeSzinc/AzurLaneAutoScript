# tests/test_meow_buy.py
import types
import pytest

@pytest.fixture
def buyer(monkeypatch):
    """
    提供一个“无真机/无UI”的 MeowfficerBuy 实例：
    - 用 DummyDevice 替换真实 Device（避免 ADB / config.args 依赖）
    - 关闭 early_ocr_import（避免访问 config.is_actual_task）
    - mock OCR（MEOWFFICER.ocr / MEOWFFICER_COINS.ocr）
    - mock meow_choose / meow_confirm（记录调用并同步扣金币）
    返回: (buyer, state, calls)
    """

    # 1) 替换基类中的 Device，并关闭 early OCR
    import module.base.base as base_mod

    # 跳过 ModuleBase.__init__ 里的 early_ocr_import
    monkeypatch.setattr(base_mod.ModuleBase, "EARLY_OCR_IMPORT", True)

    class DummyDevice:
        def __init__(self, config):
            self.config = config
            self.image = object()
        def screenshot(self): pass
        def click(self, *a, **k): pass

    monkeypatch.setattr(base_mod, "Device", DummyDevice)

    # 2) 导入被测类与常量
    from module.meowfficer.buy import (
        MeowfficerBuy, MEOWFFICER, MEOWFFICER_COINS, BUY_MAX, BUY_PRIZE
    )

    # 3) 构造最小可用 config（补齐可能访问到的字段）
    cfg = types.SimpleNamespace(
        Meowfficer_BuyAmount=2,          # 基线购买数
        Meowfficer_OverflowCoins=15000,  # 溢出阈值
        DropRecord_MeowfficerBuy="none", # meow_confirm 里会用到的字段名（已mock，不影响）
        is_actual_task=False,
        args={},                         # 真实 Device 会读 config.args；我们已用 DummyDevice，但留着以防其它路径读取
    )

    # 4) 实例化被测对象（此时会使用 DummyDevice）
    b = MeowfficerBuy(cfg)

    # 5) 可变的“系统状态”，供 OCR/购买更新
    state = {
        "remain": BUY_MAX,     # remain + bought = total
        "bought": 0,
        "total": BUY_MAX,
        "coins": 20000,        # 初始金币
        "price": BUY_PRIZE,
    }
    calls = []  # 记录每次 meow_choose(count) 的参数

    # 6) mock OCR
    monkeypatch.setattr(MEOWFFICER, "ocr",
        lambda img: (state["remain"], state["bought"], state["total"]))
    monkeypatch.setattr(MEOWFFICER_COINS, "ocr", lambda img: state["coins"])

    # 7) mock 购买/确认：一次性买 count 个，并同步扣金币/更新 bought
    def fake_meow_choose(count):
        calls.append(count)
        state["bought"] += count
        state["remain"] = state["total"] - state["bought"]
        state["coins"] -= state["price"] * count
        return True

    monkeypatch.setattr(b, "meow_choose", fake_meow_choose)
    monkeypatch.setattr(b, "meow_confirm", lambda: None)

    # 8) 静音 logger（调试时可改为 print）
    b.logger = types.SimpleNamespace(
        info=lambda *a, **k: None,
        warning=lambda *a, **k: None,
        hr=lambda *a, **k: None,
    )

    return b, state, calls


def test_overflow_extra_buy(buyer):
    """
    coins=20000, 阈值=15000, 基线=2
    基线后 coins = 20000 - 2*1500 = 17000 (>15000)
    追加 need_more = ceil((17000-15000)/1500) = 2
    期望: meow_choose 调用两次：[2, 2]；最终 coins 为 14000
    """
    b, state, calls = buyer
    ok = b.meow_buy()
    from module.meowfficer.buy import BUY_PRIZE
    assert ok is True
    assert calls == [2, 2]
    assert state["coins"] == 20000 - 4 * BUY_PRIZE


def test_equal_threshold_no_extra(buyer):
    """
    初始 coins 恰好等于阈值 → 只买基线，不追加
    """
    b, state, calls = buyer
    state["coins"] = 15000
    ok = b.meow_buy()
    assert ok is True
    assert calls == [2]


def test_low_coins_clip_to_today_left(buyer):
    """
    今日剩余额度不足：把 bought 设到 14，只能再买 1 个。
    基线会被裁剪为 1；不追加。
    """
    b, state, calls = buyer
    from module.meowfficer.buy import BUY_MAX
    state["bought"] = BUY_MAX - 1   # 已买 14/15
    state["remain"] = state["total"] - state["bought"]
    state["coins"] = 50000
    ok = b.meow_buy()
    assert ok is True
    assert calls[0] == 1            # 基线 2 被裁到 1
