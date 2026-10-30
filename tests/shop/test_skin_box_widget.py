"""Skin-box checkbox grid values keep their multi-selection through GUI saves."""
import unittest
from unittest.mock import patch

from module.webui.utils import parse_pin_value

# GUI process setup replaces PIL globally; these device-free widget tests must
# not affect real image modules used by the other shop tests in the same run.
with patch('module.webui.fake_pil_module.import_fake_pil_module'):
    from module.webui.widgets import put_arg_skin_box_slots


class TestSkinBoxSlotPinValue(unittest.TestCase):
    def test_all_positions_serialize_as_all(self):
        self.assertEqual(parse_pin_value(list(range(1, 11)), 'skin_box_slots'), 'all')

    def test_empty_selection_serialize_as_none(self):
        self.assertEqual(parse_pin_value([], 'skin_box_slots'), 'none')

    def test_single_selection_keeps_position(self):
        self.assertEqual(parse_pin_value([2], 'skin_box_slots'), '2')

    def test_multi_selection_sorted_and_deduplicated(self):
        self.assertEqual(parse_pin_value([3, 1, 3], 'skin_box_slots'), '1,3')

    def test_numeric_value_from_config_chain_supported(self):
        self.assertEqual(parse_pin_value(2, 'skin_box_slots'), '2')

    def test_invalid_selection_raises_instead_of_buying_all(self):
        for value in ([0], [11], ['invalid'], [True]):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_pin_value(value, 'skin_box_slots')

    def test_normal_boolean_checkbox_unchanged(self):
        self.assertIs(parse_pin_value([]), False)
        self.assertIs(parse_pin_value([True]), True)
        self.assertIs(parse_pin_value([], 'bool'), False)
        self.assertIs(parse_pin_value([True], 'bool'), True)

    def test_other_numeric_and_string_inputs_unchanged(self):
        self.assertEqual(parse_pin_value('10'), 10)
        self.assertEqual(parse_pin_value('all'), 'all')
        self.assertEqual(parse_pin_value('2', 'str'), '2')


class TestSkinBoxSlotWidget(unittest.TestCase):
    def render(self, value):
        with patch('module.webui.widgets.put_scope') as scope, \
                patch('module.webui.widgets.put_checkbox') as checkbox, \
                patch('module.webui.widgets.get_title_help'), \
                patch('module.webui.widgets.t', side_effect=lambda key, slot: 'Slot {}'.format(slot)):
            put_arg_skin_box_slots({'name': 'ShopFrequent_GeneralShop_SkinBoxSlots', 'value': value})
        return scope, checkbox

    def test_fixed_slot_labels_and_values(self):
        scope, checkbox = self.render('1,3')
        self.assertEqual(scope.call_args[0][0],
                         'arg_container-skin_box_slots-ShopFrequent_GeneralShop_SkinBoxSlots')
        self.assertEqual(checkbox.call_args[1]['name'], 'ShopFrequent_GeneralShop_SkinBoxSlots')
        self.assertEqual(checkbox.call_args[1]['value'], [1, 3])
        self.assertEqual(checkbox.call_args[1]['options'],
                         [{'label': 'Slot {}'.format(slot), 'value': slot} for slot in range(1, 11)])

    def test_default_all_shows_all_checked(self):
        _, checkbox = self.render('all')
        self.assertEqual(checkbox.call_args[1]['value'], list(range(1, 11)))

    def test_none_shows_no_checked_slots(self):
        _, checkbox = self.render('none')
        self.assertEqual(checkbox.call_args[1]['value'], [])

    def test_invalid_saved_value_does_not_enable_slots(self):
        _, checkbox = self.render('bad input')
        self.assertEqual(checkbox.call_args[1]['value'], [])


if __name__ == '__main__':
    unittest.main()
