"""Policy and confirmation-flow regression tests for island fish exchange."""
from types import SimpleNamespace

import pytest

import module.config.server as server
import module.island_handler.exchange as exchange_module
from module.island_handler.exchange import (
    FISH_MEAT_SOURCES,
    IslandExchange,
    fish_name_to_id,
    get_fish_exchange_amounts,
    get_fish_meat_gain,
)
from module.ui_white.assets import BACK_ARROW_WHITE


@pytest.fixture
def jp_server(monkeypatch):
    monkeypatch.setattr(server, 'server', 'jp')


@pytest.fixture
def cn_server(monkeypatch):
    monkeypatch.setattr(server, 'server', 'cn')


class TestFishMeatSources:
    def test_sources_follow_exchange_recipes(self):
        assert FISH_MEAT_SOURCES == {
            2521: {5002: 4, 5003: 3, 5004: 2, 5007: 3},
            2522: {5102: 3, 5103: 12, 5104: 5, 5105: 1, 5106: 2, 5107: 18},
        }


class TestFishNameToId:
    def test_misread_name(self, jp_server):
        # Long vowel mark dropped from サーモン
        assert fish_name_to_id('サモン', 2522) == 5104

    def test_exact_name(self, cn_server):
        assert fish_name_to_id('鲶鱼', 2521) == 5002
        assert fish_name_to_id('黄鳍金枪鱼', 2522) == 5107

    def test_ambiguous_or_empty_name(self, cn_server):
        # One glyph away from every freshwater fish
        assert fish_name_to_id('X鱼', 2521) is None
        assert fish_name_to_id('', 2521) is None


class TestExchangeAmounts:
    def test_fish_keep_items(self):
        values = {'IslandProduction.IslandProduction.HardFloorItems': '{2000: 100, 5107: 3}'}
        exchange = object.__new__(IslandExchange)
        exchange.config = SimpleNamespace(cross_get=lambda key, default=None: values.get(key, default))

        assert exchange.get_fish_keep_items() == {5107: 3}

    def test_keep(self):
        amounts = get_fish_exchange_amounts({5105: 4, 5107: 10}, keep={5107: 3, 5103: 5})
        assert amounts == {5105: 4, 5107: 7}
        assert get_fish_meat_gain(amounts) == 4 * 1 + 7 * 18

    def test_keep_more_than_stock(self):
        assert get_fish_exchange_amounts({5107: 2}, keep={5107: 5}) == {5107: 0}

    def test_no_keep(self):
        assert get_fish_exchange_amounts({5107: 2}) == {5107: 2}
        assert get_fish_exchange_amounts({5107: 2}, keep={5107: -1}) == {5107: 2}


class TestExchangeConfirm:
    @staticmethod
    def make_exchange(monkeypatch, frames, popup_frames=(), white_band_frames=(), level_up_frames=()):
        """
        Args:
            frames (list): Fish meat (owned, gain), or None while a popup covers it.
            popup_frames (set[int]): Screenshots where the confirm popup is clicked.
            white_band_frames (set[int]): Screenshots where the item popup has a white band.
            level_up_frames (set[int]): Screenshots where a level-up popup is handled.
        """
        exchange = object.__new__(IslandExchange)
        exchange.frame = -1
        exchange.confirm_clicks = []
        exchange.clicks = []
        exchange.device = SimpleNamespace(
            image=None, click=lambda button: exchange.clicks.append((exchange.frame, button)))

        def loop(skip_first=True, timeout=None):
            for exchange.frame in range(len(frames)):
                yield None

        def appear_then_click(button, offset=0, interval=0):
            exchange.confirm_clicks.append(exchange.frame)
            return True

        exchange.loop = loop
        # The exchange item-change popup is handled by the white-band detector;
        # GET_ITEMS_1 does not match it.
        exchange.appear = lambda *args, **kwargs: False
        exchange.has_white_band = lambda: exchange.frame in white_band_frames
        exchange.handle_island_level_up = lambda: exchange.frame in level_up_frames
        exchange.handle_island_popup_confirm = lambda name='': exchange.frame in popup_frames
        exchange.appear_then_click = appear_then_click
        monkeypatch.setattr(exchange_module, 'read_fish_meat', lambda image: frames[exchange.frame])
        return exchange

    def test_misread_while_popup_fades(self, monkeypatch):
        # From a device log: 13052 +24 read as 1305224 while the popup fades in,
        # and the page keeps showing +24 for a while after the popup is confirmed
        frames = [(13052, 24), (1305224, 0), None, (13052, 24), None, (13052, 24), (13076, 0)]
        exchange = self.make_exchange(monkeypatch, frames, popup_frames={2}, white_band_frames={4})
        assert exchange._exchange_confirm(2522, 13052, 24) == 13076
        # 加工 is not clicked again once the popup is confirmed
        assert all(frame < 2 for frame in exchange.confirm_clicks)

    def test_gain_not_seen(self, monkeypatch):
        frames = [(13052, 24), None, None, (13052, 24)]
        exchange = self.make_exchange(monkeypatch, frames, popup_frames={1}, white_band_frames={2})
        assert exchange._exchange_confirm(2522, 13052, 24) is None

    def test_matching_digits_without_item_popup_fail(self, monkeypatch):
        frames = [(0, 24), None, (24, 0), (24, 0)]
        exchange = self.make_exchange(monkeypatch, frames, popup_frames={1})
        assert exchange._exchange_confirm(2522, 0, 24) is None

    def test_waits_for_item_popup_before_returning(self, monkeypatch):
        frames = [(0, 24), None, (24, 0), (24, 0), None, (24, 0)]
        exchange = self.make_exchange(
            monkeypatch, frames, popup_frames={1}, white_band_frames={4})
        assert exchange._exchange_confirm(2522, 0, 24) == 24
        assert [frame for frame, _ in exchange.clicks] == [4]
        assert exchange.frame == 5

    def test_waits_for_item_popup_to_disappear_before_back(self, monkeypatch):
        frames = [(0, 24), None, None, None, (24, 0)]
        exchange = self.make_exchange(
            monkeypatch, frames, popup_frames={1}, white_band_frames={2, 3})
        assert exchange._exchange_confirm(2522, 0, 24) == 24
        exchange.ui_click = lambda click_button, **kwargs: exchange.device.click(click_button)
        exchange.ui_back(check_button=object())
        assert [frame for frame, _ in exchange.clicks] == [2, 3, 4]
        assert exchange.clicks[-1][1] is BACK_ARROW_WHITE

    def test_level_up_does_not_replace_item_popup(self, monkeypatch):
        frames = [(0, 24), None, None, (24, 0)]
        exchange = self.make_exchange(monkeypatch, frames, popup_frames={1}, level_up_frames={2})
        assert exchange._exchange_confirm(2522, 0, 24) is None

    def test_does_not_exchange_again_after_item_popup(self, monkeypatch):
        frames = [(0, 24), None, (0, 24), (24, 0)]
        exchange = self.make_exchange(monkeypatch, frames, white_band_frames={1})
        assert exchange._exchange_confirm(2522, 0, 24) == 24
        assert exchange.confirm_clicks == [0]

    def test_missing_item_popup_fails_even_when_no_gain_is_required(self, monkeypatch):
        exchange = self.make_exchange(monkeypatch, [(0, 1), (1, 0), (1, 0)])
        exchange.island_shop_side_navbar_ensure = lambda **kwargs: True
        exchange._exchange_clear_selection = lambda: 0
        exchange._exchange_read_cards = lambda meat_id: [(0, 5105, 1)]
        exchange._exchange_select_all = lambda: True
        exchange._exchange_set_count = lambda index, amount: True
        monkeypatch.setattr(exchange_module, 'read_fish_counts', lambda image, indices: [1])
        assert not exchange.island_shop_exchange({2522: 0})
