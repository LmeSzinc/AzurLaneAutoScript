from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from module.equipment.assets import EQUIPMENT_CODE_ENTER, EQUIPMENT_CODE_EXPORT, EQUIPMENT_CODE_TEXTBOX
from module.equipment.equipment_code import EquipmentCodeHandler
from module.exception import RequestHumanTakeover


@pytest.fixture
def handler():
    handler = object.__new__(EquipmentCodeHandler)
    handler.config = SimpleNamespace(EquipmentCode_ExportToConfig=True)
    handler.device = Mock()
    handler.device.input_text.return_value = None
    handler.device.ensure_clipboard.return_value = None
    handler.loop = Mock(return_value=range(3))
    handler.is_code_preview_loaded = Mock(return_value=False)
    handler.appear_then_click = Mock(return_value=True)
    handler.handle_info_bar = Mock()
    handler.info_bar_count = Mock(return_value=1)
    handler.device.get_clipboard.return_value = 'exported code'
    return handler


def test_code_input_requires_preview_after_input_and_keyboard_dismissal(handler):
    handler.device.is_keyboard_shown.side_effect = [True, False, False]
    handler.is_code_preview_loaded.side_effect = [False, True]

    assert handler._code_input('equipment code') is True
    handler.device.input_text.assert_called_once_with('equipment code', EQUIPMENT_CODE_TEXTBOX)
    handler.appear_then_click.assert_called_once_with(EQUIPMENT_CODE_ENTER, offset=(5, 5), interval=3)


@pytest.mark.parametrize('operation', ['input_text', 'ensure_clipboard', 'get_clipboard'])
def test_device_takeover_propagates(handler, operation):
    getattr(handler.device, operation).side_effect = RequestHumanTakeover

    with pytest.raises(RequestHumanTakeover):
        if operation == 'input_text':
            handler._code_input('equipment code')
        else:
            handler._code_export()
    if operation == 'input_text':
        handler.loop.assert_not_called()
        handler.appear_then_click.assert_not_called()


@pytest.mark.parametrize('clipboard', ['exported code', ''])
def test_export_orders_prepare_copy_completion_and_read_and_rejects_empty(handler, clipboard):
    handler.loop.return_value = range(2)
    handler.device.get_clipboard.return_value = clipboard
    order = Mock()
    order.attach_mock(handler.device.ensure_clipboard, 'prepare')
    order.attach_mock(handler.appear_then_click, 'copy')
    order.attach_mock(handler.device.get_clipboard, 'read')

    assert handler._code_export() == (clipboard or None)
    assert order.mock_calls == [
        call.prepare(), call.copy(EQUIPMENT_CODE_EXPORT, offset=(5, 5), interval=3), call.read(),
    ]


@pytest.mark.parametrize('clicked,completion', [
    (False, 1), (True, 0),
])
def test_export_requires_copy_and_completion(handler, clicked, completion):
    handler.appear_then_click.return_value = clicked
    handler.info_bar_count.return_value = completion

    assert handler._code_export() is None
    handler.device.get_clipboard.assert_not_called()


def test_failed_export_does_not_save_or_apply_equipment_code(handler):
    handler.last_code = 'previous code'
    handler._code_enter = Mock()
    handler.get_code = Mock(return_value=None)
    handler.set_code = Mock()
    handler._code_export = Mock(return_value=None)
    handler._code_apply = Mock(return_value=True)

    assert handler.code_clear(name='bogue') is False
    assert handler.last_code == 'previous code'
    handler.set_code.assert_not_called()
    handler._code_apply.assert_not_called()
