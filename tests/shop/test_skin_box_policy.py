"""Persistent quota and scripted real-clerk confirmation tests, without devices."""
import json
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from module.combat.assets import GET_ITEMS_1, GET_ITEMS_3
from module.shop.assets import SHOP_BUY_CONFIRM
from module.shop.clerk import ShopClerk
from module.shop.shop_general import GeneralShop_250814
from module.ui.assets import SHOP_BACK_ARROW

from test_general import make_item
from test_skin_box_config import temporary_shop_config


def configured_shop(config):
    shop = GeneralShop_250814.__new__(GeneralShop_250814)
    shop.config = config
    shop._currency = 600000
    shop.gems = 10000
    return shop


def confirmed_purchase(shop, item, skip_first_screenshot=True):
    shop.shop_buy_confirmed(item)
    return True


class TestSkinBoxPurchaseQuota(unittest.TestCase):
    def settings(self, **overrides):
        values = {'BuySkinBox': True, 'SkinBoxSlots': 'all',
                  'SkinBoxPurchaseLimit': 2, 'SkinBoxPurchaseCount': 0,
                  'ConsumeCoins': True, 'UseGems': True,
                  'Filter': 'BookRedT3 > BoxIrisT2'}
        values.update(overrides)
        return values

    def test_confirmed_purchase_persists_once_across_config_instances(self):
        with temporary_shop_config(self.settings()) as (filename, load):
            shop = configured_shop(load())
            item = make_item(shop)

            def repeated_reward_frames(clerk, selected, skip_first_screenshot=True):
                clerk.shop_buy_confirmed(selected)
                clerk.shop_buy_confirmed(selected)
                return True

            with patch.object(ShopClerk, 'shop_buy_execute', repeated_reward_frames):
                shop.shop_buy_execute(item)
            self.assertEqual(load().GeneralShop_SkinBoxPurchaseCount, 1)
            with open(filename, encoding='utf-8') as handle:
                self.assertEqual(json.load(handle)['ShopFrequent']['GeneralShop']['SkinBoxPurchaseCount'], 1)

    def test_limit_auto_stops_and_blocks_unknown_skin_boxes_same_run(self):
        with temporary_shop_config(self.settings(SkinBoxPurchaseLimit=1)) as (_, load):
            shop = configured_shop(load())
            item = make_item(shop)
            with patch.object(ShopClerk, 'shop_buy_execute', confirmed_purchase):
                shop.shop_buy_execute(item)
            latest = load()
            self.assertEqual(latest.GeneralShop_SkinBoxPurchaseCount, 1)
            self.assertIs(latest.GeneralShop_BuySkinBox, False)
            self.assertIs(latest.cross_get('ShopFrequent.Storage.Storage.SkinBoxQuota')['stopped'], True)
            for name in ('1', '2', '3'):
                with self.subTest(name=name):
                    self.assertIsNone(shop.shop_get_item_to_buy([make_item(shop, name=name)]))
            ordinary = make_item(shop, slot=(2, 1), name='BookRedT3', price=2400)
            self.assertIs(shop.shop_get_item_to_buy([make_item(shop), ordinary]), ordinary)

    def test_limit_remains_reached_after_new_shop_instance(self):
        with temporary_shop_config(self.settings(SkinBoxPurchaseLimit=1)) as (_, load):
            first = configured_shop(load())
            with patch.object(ShopClerk, 'shop_buy_execute', confirmed_purchase):
                first.shop_buy_execute(make_item(first))
            second = configured_shop(load())
            self.assertIsNone(second.shop_get_item_to_buy([make_item(second)]))
            self.assertEqual(second.config.GeneralShop_SkinBoxPurchaseCount, 1)

    def test_successful_count_and_stop_persist_into_another_process(self):
        with temporary_shop_config(self.settings(SkinBoxPurchaseLimit=1)) as (filename, load):
            shop = configured_shop(load())
            with patch.object(ShopClerk, 'shop_buy_execute', confirmed_purchase):
                shop.shop_buy_execute(make_item(shop))
            # A fresh interpreter must read persisted JSON, not in-memory state.
            script = '''
import json
import sys
from unittest.mock import patch
from module.config.config import AzurLaneConfig
resolver = lambda config_name, mod_name='alas': sys.argv[1]
with patch('module.config.config_updater.filepath_config', resolver), patch('module.config.config.filepath_config', resolver):
    config = AzurLaneConfig('unit-shop', task='ShopFrequent')
    print('QUOTA_RESULT:' + json.dumps([config.GeneralShop_SkinBoxPurchaseCount, config.GeneralShop_BuySkinBox, config.cross_get('ShopFrequent.Storage.Storage.SkinBoxQuota')['stopped']]))
'''
            output = subprocess.check_output([sys.executable, '-c', script, filename], universal_newlines=True)
            result = next(line[len('QUOTA_RESULT:'):] for line in output.splitlines()
                          if line.startswith('QUOTA_RESULT:'))
            self.assertEqual(json.loads(result), [1, False, True])

    def test_unlimited_mode_still_records_successes(self):
        with temporary_shop_config(self.settings(SkinBoxPurchaseLimit=0)) as (_, load):
            shop = configured_shop(load())
            with patch.object(ShopClerk, 'shop_buy_execute', confirmed_purchase):
                shop.shop_buy_execute(make_item(shop))
                shop.shop_buy_execute(make_item(shop, slot=(1, 0)))
            self.assertEqual(load().GeneralShop_SkinBoxPurchaseCount, 2)
            self.assertIs(load().GeneralShop_BuySkinBox, True)

    def test_unconfirmed_return_does_not_count_or_allow_another_skin_box(self):
        for result in (False, None):
            with self.subTest(result=result), temporary_shop_config(self.settings()) as (_, load):
                shop = configured_shop(load())
                with patch.object(ShopClerk, 'shop_buy_execute', return_value=result):
                    shop.shop_buy_execute(make_item(shop))
                self.assertEqual(load().GeneralShop_SkinBoxPurchaseCount, 0)
                skin = make_item(shop, slot=(1, 0), name='2')
                self.assertIsNone(shop.shop_get_item_to_buy([skin]))
                ordinary = make_item(shop, slot=(2, 1), name='BookRedT3', price=2400)
                self.assertIs(shop.shop_get_item_to_buy([skin, ordinary]), ordinary)

    def test_failed_operation_does_not_consume_persistent_quota(self):
        with temporary_shop_config(self.settings()) as (_, load):
            shop = configured_shop(load())
            with patch.object(ShopClerk, 'shop_buy_execute', side_effect=RuntimeError('unconfirmed')):
                with self.assertRaises(RuntimeError):
                    shop.shop_buy_execute(make_item(shop))
            self.assertEqual(load().GeneralShop_SkinBoxPurchaseCount, 0)

    def test_confirmed_purchase_stays_counted_when_later_processing_raises(self):
        with temporary_shop_config(self.settings()) as (_, load):
            shop = configured_shop(load())

            def receipt_then_error(clerk, item, skip_first_screenshot=True):
                clerk.shop_buy_confirmed(item)
                clerk.shop_buy_confirmed(item)
                raise RuntimeError('error after confirmed receipt')

            with patch.object(ShopClerk, 'shop_buy_execute', receipt_then_error):
                with self.assertRaises(RuntimeError):
                    shop.shop_buy_execute(make_item(shop))
            self.assertEqual(load().GeneralShop_SkinBoxPurchaseCount, 1)
            # Confirmation already succeeded; a later error is not an
            # unconfirmed operation that should block the next allowed box.
            next_skin = make_item(shop, slot=(1, 0), name='2')
            self.assertIs(shop.shop_get_item_to_buy([next_skin]), next_skin)

    def test_ordinary_purchase_does_not_increment_skin_count(self):
        with temporary_shop_config(self.settings()) as (_, load):
            shop = configured_shop(load())
            ordinary = make_item(shop, name='BookRedT3', price=2400)
            with patch.object(ShopClerk, 'shop_buy_execute', confirmed_purchase):
                shop.shop_buy_execute(ordinary)
            self.assertEqual(load().GeneralShop_SkinBoxPurchaseCount, 0)

    def test_confirmed_support_crate_purchase_does_not_increment_skin_count(self):
        for name in ('BoxIrisT2', 'BoxSardegnaT2'):
            with self.subTest(name=name), temporary_shop_config(self.settings()) as (_, load):
                shop = configured_shop(load())
                support = make_item(shop, slot=(3, 1), name=name, price=900)
                with patch.object(ShopClerk, 'shop_buy_execute', confirmed_purchase):
                    shop.shop_buy_execute(support)
                self.assertEqual(load().GeneralShop_SkinBoxPurchaseCount, 0)

    def test_reached_skin_quota_keeps_support_filter_and_overflow_purchases(self):
        with temporary_shop_config(self.settings(SkinBoxPurchaseLimit=1,
                                                SkinBoxPurchaseCount=1,
                                                ConsumeCoins=False)) as (_, load):
            shop = configured_shop(load())
            iris = make_item(shop, slot=(3, 1), name='BoxIrisT2', price=900)
            self.assertIs(shop.shop_get_item_to_buy([make_item(shop), iris]), iris)
            shop.config.GeneralShop_ConsumeCoins = True
            sardegna = make_item(shop, slot=(3, 1), name='BoxSardegnaT2', price=900)
            self.assertIs(shop.shop_get_item_to_buy([make_item(shop), sardegna]), sardegna)
            self.assertEqual(load().GeneralShop_SkinBoxPurchaseCount, 1)

    def test_invalid_limit_or_count_blocks_only_cosmetics(self):
        for key in ('SkinBoxPurchaseLimit', 'SkinBoxPurchaseCount'):
            for value in (-1, True, 'broken', 1.5):
                with self.subTest(key=key, value=value), \
                        temporary_shop_config(self.settings(**{key: value})) as (_, load):
                    shop = configured_shop(load())
                    skin = make_item(shop)
                    ordinary = make_item(shop, name='BookRedT3', price=2400)
                    self.assertIs(shop.shop_get_item_to_buy([skin, ordinary]), ordinary)

    def test_scans_and_restarts_do_not_reset_count(self):
        with temporary_shop_config(self.settings(SkinBoxPurchaseCount=1)) as (_, load):
            for _ in range(3):
                shop = configured_shop(load())
                item = make_item(shop)
                self.assertIs(shop.shop_get_item_to_buy([item]), item)
                self.assertEqual(load().GeneralShop_SkinBoxPurchaseCount, 1)

    def test_reenable_after_auto_stop_starts_a_new_cycle(self):
        with temporary_shop_config(self.settings(BuySkinBox=False, SkinBoxPurchaseCount=2),
                                   {'SkinBoxQuota': {'epoch': 'old', 'stopped': True}}) as (_, load):
            config = load()
            config.GeneralShop_BuySkinBox = True
            shop = configured_shop(load())
            item = make_item(shop)
            self.assertIs(shop.shop_get_item_to_buy([item]), item)
            self.assertEqual(load().GeneralShop_SkinBoxPurchaseCount, 0)
            self.assertIs(load().cross_get('ShopFrequent.Storage.Storage.SkinBoxQuota')['stopped'], False)

    def test_manual_zero_count_reopens_without_accidental_cycle_reset(self):
        with temporary_shop_config(self.settings(SkinBoxPurchaseCount=1, SkinBoxPurchaseLimit=1),
                                   {'SkinBoxQuota': {'epoch': 'manual', 'stopped': False}}) as (_, load):
            config = load()
            self.assertIsNone(configured_shop(config).shop_get_item_to_buy([make_item(configured_shop(config))]))
            config.GeneralShop_SkinBoxPurchaseCount = 0
            config.GeneralShop_BuySkinBox = True
            shop = configured_shop(load())
            item = make_item(shop)
            self.assertIs(shop.shop_get_item_to_buy([item]), item)
            self.assertEqual(load().GeneralShop_SkinBoxPurchaseCount, 0)

    def test_epoch_changed_during_operation_preserves_new_user_cycle(self):
        with temporary_shop_config(self.settings(),
                                   {'SkinBoxQuota': {'epoch': 'before', 'stopped': False}}) as (_, load):
            shop = configured_shop(load())

            def reset_during_purchase(clerk, item, skip_first_screenshot=True):
                other = load()
                with other.multi_set():
                    other.GeneralShop_SkinBoxPurchaseCount = 0
                    other.cross_set('ShopFrequent.Storage.Storage.SkinBoxQuota',
                                    {'epoch': 'new-cycle', 'stopped': False})
                clerk.shop_buy_confirmed(item)
                return True

            with patch.object(ShopClerk, 'shop_buy_execute', reset_during_purchase):
                shop.shop_buy_execute(make_item(shop))
            self.assertEqual(load().GeneralShop_SkinBoxPurchaseCount, 0)
            self.assertEqual(load().cross_get('ShopFrequent.Storage.Storage.SkinBoxQuota')['epoch'], 'new-cycle')

    def test_confirmation_honors_latest_limit(self):
        with temporary_shop_config(self.settings(SkinBoxPurchaseLimit=5)) as (_, load):
            shop = configured_shop(load())

            def lower_limit_during_purchase(clerk, item, skip_first_screenshot=True):
                other = load()
                other.GeneralShop_SkinBoxPurchaseLimit = 1
                clerk.shop_buy_confirmed(item)
                return True

            with patch.object(ShopClerk, 'shop_buy_execute', lower_limit_during_purchase):
                shop.shop_buy_execute(make_item(shop))
            self.assertEqual(load().GeneralShop_SkinBoxPurchaseCount, 1)
            self.assertIs(load().GeneralShop_BuySkinBox, False)

    def test_invalid_positions_saved_mid_purchase_do_not_erase_confirmed_count(self):
        with temporary_shop_config(self.settings()) as (_, load):
            shop = configured_shop(load())

            def invalidate_positions_during_purchase(clerk, item, skip_first_screenshot=True):
                other = load()
                other.GeneralShop_SkinBoxSlots = 'broken'
                clerk.shop_buy_confirmed(item)
                return True

            with patch.object(ShopClerk, 'shop_buy_execute', invalidate_positions_during_purchase):
                shop.shop_buy_execute(make_item(shop))
            latest = load()
            self.assertEqual(latest.GeneralShop_SkinBoxPurchaseCount, 1)
            self.assertEqual(latest.GeneralShop_SkinBoxSlots, 'broken')
            skin = make_item(shop, name='2')
            ordinary = make_item(shop, slot=(2, 1), name='BookRedT3', price=2400)
            self.assertIsNone(shop.shop_get_item_to_buy([skin]))
            self.assertIs(shop.shop_get_item_to_buy([skin, ordinary]), ordinary)

    def test_invalid_limit_saved_mid_purchase_still_counts_without_reenabling(self):
        with temporary_shop_config(self.settings()) as (_, load):
            shop = configured_shop(load())

            def invalidate_limit_during_purchase(clerk, item, skip_first_screenshot=True):
                other = load()
                with other.multi_set():
                    other.GeneralShop_SkinBoxPurchaseLimit = 'broken'
                    other.GeneralShop_BuySkinBox = False
                clerk.shop_buy_confirmed(item)
                return True

            with patch.object(ShopClerk, 'shop_buy_execute', invalidate_limit_during_purchase):
                shop.shop_buy_execute(make_item(shop))
            latest = load()
            self.assertEqual(latest.GeneralShop_SkinBoxPurchaseCount, 1)
            self.assertEqual(latest.GeneralShop_SkinBoxPurchaseLimit, 'broken')
            self.assertIs(latest.GeneralShop_BuySkinBox, False)
            skin = make_item(shop, name='2')
            ordinary = make_item(shop, slot=(2, 1), name='BookRedT3', price=2400)
            self.assertIsNone(shop.shop_get_item_to_buy([skin]))
            self.assertIs(shop.shop_get_item_to_buy([skin, ordinary]), ordinary)


class TestShopClerkPurchaseSignals(unittest.TestCase):
    def scripted_clerk(self, frames):
        clerk = ShopClerk.__new__(ShopClerk)
        current = {'index': 0}

        def screenshot():
            current['index'] += 1
            if current['index'] >= len(frames):
                raise RuntimeError('scripted frames exhausted')

        def appear(button, **kwargs):
            frame = frames[current['index']]
            if button is SHOP_BACK_ARROW:
                return (frame == 'start' or frame == 'end' and 'interval' not in kwargs)
            if button is GET_ITEMS_1:
                return frame == 'reward1'
            if button is GET_ITEMS_3:
                return frame == 'reward3'
            return False

        clerk.device = SimpleNamespace(screenshot=screenshot, click=Mock())
        clerk.appear = Mock(side_effect=appear)
        clerk.appear_then_click = Mock(side_effect=lambda button, **kwargs:
                                      button is SHOP_BUY_CONFIRM and frames[current['index']] == 'confirm')
        clerk.shop_interval_clear = Mock()
        clerk.interval_reset = Mock()
        clerk.shop_buy_handle = Mock(return_value=False)
        clerk.handle_retirement = Mock(return_value=False)
        clerk.shop_obstruct_handle = Mock(side_effect=lambda:
                                         frames[current['index']] in ('popup', 'reward1', 'reward3'))
        clerk.info_bar_count = Mock(side_effect=lambda: frames[current['index']] == 'info')
        clerk.shop_buy_confirmed = Mock()
        return clerk

    def test_confirm_then_reward_calls_hook_once_for_repeated_reward_frames(self):
        for frame in ('reward1', 'reward3'):
            with self.subTest(frame=frame):
                clerk = self.scripted_clerk(['start', 'confirm', frame, frame, 'end'])
                item = object()
                ShopClerk.shop_buy_execute(clerk, item)
                clerk.shop_buy_confirmed.assert_called_once_with(item)

    def test_generic_popup_and_info_bar_do_not_confirm_purchase(self):
        for frame in ('popup', 'info'):
            with self.subTest(frame=frame):
                clerk = self.scripted_clerk(['start', 'confirm', frame, 'end'])
                ShopClerk.shop_buy_execute(clerk, object())
                clerk.shop_buy_confirmed.assert_not_called()

    def test_reward_overlay_without_purchase_confirm_does_not_count(self):
        clerk = self.scripted_clerk(['reward1', 'end'])
        ShopClerk.shop_buy_execute(clerk, object())
        clerk.shop_buy_confirmed.assert_not_called()


if __name__ == '__main__':
    unittest.main()
