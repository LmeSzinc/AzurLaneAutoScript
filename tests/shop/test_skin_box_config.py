"""Exercise the actual configuration parser, migration and JSON persistence."""
import json
import os
import tempfile
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from module.config.config import AzurLaneConfig
from module.config.config_updater import ConfigUpdater
from module.config.deep import deep_get
from module.shop.skin_box import parse_skin_box_slots


@contextmanager
def temporary_shop_config(settings=None, storage=None):
    """Real config loading/saving, redirected only to a temporary JSON file."""
    with tempfile.TemporaryDirectory(prefix='alas-shop-test-') as folder:
        filename = os.path.join(folder, 'test.json')
        data = {'ShopFrequent': {'GeneralShop': dict(settings or {})}}
        if storage is not None:
            data['ShopFrequent']['Storage'] = {'Storage': storage}
        with open(filename, 'w', encoding='utf-8') as handle:
            json.dump(data, handle)

        def resolver(config_name, mod_name='alas'):
            return filename

        with patch('module.config.config_updater.filepath_config', resolver), \
                patch('module.config.config.filepath_config', resolver):
            yield filename, lambda: AzurLaneConfig('unit-shop', task='ShopFrequent')


class TestSkinBoxSlotsParser(unittest.TestCase):
    def test_all_and_none(self):
        self.assertEqual(parse_skin_box_slots('all'), frozenset(range(1, 11)))
        self.assertEqual(parse_skin_box_slots('none'), frozenset())

    def test_single_numeric_config_value(self):
        self.assertEqual(parse_skin_box_slots(2), frozenset({2}))
        self.assertEqual(parse_skin_box_slots('2'), frozenset({2}))

    def test_comma_list_whitespace_and_duplicates(self):
        self.assertEqual(parse_skin_box_slots(' 10, 1,3,3 '), frozenset({1, 3, 10}))

    def test_balanced_wrappers_and_nfkc_punctuation(self):
        for value in ('(1,3)', '[1,3]', '（１，３）', '［１，３］'):
            with self.subTest(value=value):
                self.assertEqual(parse_skin_box_slots(value), frozenset({1, 3}))

    def test_invalid_values_fail_instead_of_selecting_all(self):
        for value in ('', '  ', '()', '[]', '(1,3]', '[1,3)', '(1,3', '1,3)',
                      '0', '11', '1,11', '1,bad', '1,,3', '1,', ',1',
                      True, False, None, 2.0, ['1', '3'], {'1': True}):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_skin_box_slots(value)


class TestSkinBoxConfigMigration(unittest.TestCase):
    def normalized(self, settings):
        return ConfigUpdater().config_update({'ShopFrequent': {'GeneralShop': settings}})

    def group(self, settings):
        return self.normalized(settings)['ShopFrequent']['GeneralShop']

    def test_generated_defaults_keep_unlimited_legacy_behavior(self):
        values = self.group({})
        self.assertEqual(values['SkinBoxSlots'], 'all')
        self.assertEqual(values['SkinBoxPurchaseLimit'], 0)
        self.assertEqual(values['SkinBoxPurchaseCount'], 0)

    def test_actual_updater_parses_numeric_text_to_integer(self):
        value = self.group({'SkinBoxSlots': '2'})['SkinBoxSlots']
        self.assertIs(type(value), int)
        self.assertEqual(parse_skin_box_slots(value), frozenset({2}))

    def test_actual_updater_empty_value_uses_default(self):
        value = self.group({'SkinBoxSlots': ''})['SkinBoxSlots']
        self.assertEqual(value, 'all')
        self.assertEqual(parse_skin_box_slots(value), frozenset(range(1, 11)))

    def test_old_true_false_migrate_only_when_new_key_is_absent(self):
        for old, expected in ((True, frozenset({1})), (False, frozenset(range(1, 11)))):
            with self.subTest(old=old):
                values = self.group({'SkinBoxFirstOnly': old})
                self.assertEqual(parse_skin_box_slots(values['SkinBoxSlots']), expected)
                self.assertNotIn('SkinBoxFirstOnly', values)

    def test_explicit_new_value_takes_priority_over_old_boolean(self):
        for value in ('2,4', 'none', 'all', '', None):
            with self.subTest(value=value):
                actual = self.group({'SkinBoxFirstOnly': True, 'SkinBoxSlots': value})['SkinBoxSlots']
                self.assertEqual(parse_skin_box_slots(actual),
                                 parse_skin_box_slots(value if value else 'all'))

    def test_legacy_migration_is_idempotent_across_two_updates(self):
        for old in (True, False):
            with self.subTest(old=old):
                once = self.normalized({'SkinBoxFirstOnly': old})
                twice = ConfigUpdater().config_update(once)
                self.assertEqual(twice['ShopFrequent']['GeneralShop'],
                                 once['ShopFrequent']['GeneralShop'])
                self.assertNotIn('SkinBoxFirstOnly', twice['ShopFrequent']['GeneralShop'])

    def test_explicit_invalid_new_value_does_not_revert_to_legacy(self):
        for value in ('1,bad', 0, 11, True):
            with self.subTest(value=value):
                actual = self.group({'SkinBoxFirstOnly': True, 'SkinBoxSlots': value})['SkinBoxSlots']
                with self.assertRaises(ValueError):
                    parse_skin_box_slots(actual)

    def test_stored_quota_survives_normalization(self):
        old = {'ShopFrequent': {
            'GeneralShop': {'SkinBoxPurchaseCount': 3},
            'Storage': {'Storage': {'SkinBoxQuota': {'epoch': 'cycle-one', 'stopped': True}}},
        }}
        normalized = ConfigUpdater().config_update(old)
        self.assertEqual(deep_get(normalized, 'ShopFrequent.GeneralShop.SkinBoxPurchaseCount'), 3)
        self.assertEqual(deep_get(normalized, 'ShopFrequent.Storage.Storage.SkinBoxQuota'),
                         {'epoch': 'cycle-one', 'stopped': True})

    def test_gui_enable_resets_count_and_marks_new_cycle(self):
        changes = dict(ConfigUpdater().save_callback('ShopFrequent.GeneralShop.BuySkinBox', True))
        self.assertEqual(changes['ShopFrequent.GeneralShop.SkinBoxPurchaseCount'], 0)
        self.assertTrue(changes['ShopFrequent.Storage.Storage.SkinBoxQuota.epoch'])
        self.assertIs(changes['ShopFrequent.Storage.Storage.SkinBoxQuota.stopped'], False)

    def test_gui_count_zero_is_an_explicit_new_cycle(self):
        changes = dict(ConfigUpdater().save_callback('ShopFrequent.GeneralShop.SkinBoxPurchaseCount', 0))
        self.assertTrue(changes['ShopFrequent.Storage.Storage.SkinBoxQuota.epoch'])
        self.assertIs(changes['ShopFrequent.Storage.Storage.SkinBoxQuota.stopped'], False)

    def test_real_config_reload_preserves_count_and_cycle(self):
        with temporary_shop_config({'SkinBoxSlots': '2', 'SkinBoxPurchaseCount': 1},
                                   {'SkinBoxQuota': {'epoch': 'stable', 'stopped': False}}) as (_, load):
            first = load()
            self.assertEqual(first.GeneralShop_SkinBoxSlots, 2)
            first.GeneralShop_SkinBoxPurchaseCount = 2
            second = load()
            self.assertEqual(second.GeneralShop_SkinBoxPurchaseCount, 2)
            self.assertEqual(second.cross_get('ShopFrequent.Storage.Storage.SkinBoxQuota')['epoch'], 'stable')


if __name__ == '__main__':
    unittest.main()
