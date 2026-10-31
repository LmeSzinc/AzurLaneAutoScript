from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest
from filelock import FileLock, Timeout

import module.device.input as input_module
from module.device.input import Input
from module.equipment.assets import EQUIPMENT_CODE_ENTER, EQUIPMENT_CODE_EXPORT, EQUIPMENT_CODE_TEXTBOX
from module.equipment.equipment_code import EquipmentCodeHandler


@pytest.fixture(autouse=True)
def clipboard_lock_file(monkeypatch, tmp_path):
    monkeypatch.setattr(input_module, '_CLIPBOARD_LOCK_FILE', str(tmp_path / 'clipboard.lock'))


def make_handler():
    handler = object.__new__(EquipmentCodeHandler)
    handler.config = SimpleNamespace(Emulator_ControlMethod='minitouch', EquipmentCode_ExportToConfig=True)
    handler.device = Mock(spec=[
        'text_input_supported', 'input_text', 'is_keyboard_shown', 'ensure_clipboard', 'get_clipboard', 'clipboard_copy',
    ])
    handler.device.clipboard_copy.side_effect = lambda copy: Input.clipboard_copy(handler.device, copy, timeout=0)
    handler.loop = Mock(return_value=range(3))
    handler.is_code_preview_loaded = Mock(return_value=False)
    handler.appear_then_click = Mock(return_value=True)
    return handler


@pytest.mark.parametrize('supported', [False, True])
def test_equipment_uses_device_input_capability(supported):
    handler = make_handler()
    handler.device.text_input_supported.return_value = supported

    assert handler.equipment_code_supported() is supported


def test_input_leaves_keyboard_and_preview_checks_to_respective_layers():
    handler = make_handler()
    handler.device.input_text.return_value = True
    handler.device.is_keyboard_shown.side_effect = [True, False, False]
    handler.is_code_preview_loaded.side_effect = [False, True]

    assert handler._code_input('equipment code') is True
    handler.device.input_text.assert_called_once_with('equipment code', EQUIPMENT_CODE_TEXTBOX)
    handler.appear_then_click.assert_called_once_with(EQUIPMENT_CODE_ENTER, offset=(5, 5), interval=3)
    handler.loop.assert_called_once_with(timeout=10, skip_first=False)


def test_input_failure_skips_preview_loop():
    handler = make_handler()
    handler.device.input_text.return_value = False

    assert handler._code_input('equipment code') is False
    handler.loop.assert_not_called()
    handler.appear_then_click.assert_not_called()


def test_successful_device_input_still_requires_equipment_preview():
    handler = make_handler()
    handler.device.input_text.return_value = True
    handler.device.is_keyboard_shown.return_value = False

    assert handler._code_input('equipment code') is False


def test_export_prepares_clipboard_access_before_copy_and_reads_device_clipboard():
    handler = make_handler()
    handler.handle_info_bar = Mock()
    handler.info_bar_count = Mock(side_effect=[0, 1])
    handler.device.ensure_clipboard.return_value = True
    handler.device.get_clipboard.return_value = 'exported code'
    order = Mock()
    order.attach_mock(handler.device.ensure_clipboard, 'prepare')
    order.attach_mock(handler.appear_then_click, 'copy')
    order.attach_mock(handler.device.get_clipboard, 'read')

    def copy(*args, **kwargs):
        with pytest.raises(Timeout):
            with FileLock(input_module._CLIPBOARD_LOCK_FILE, timeout=0):
                pass
        return True

    handler.appear_then_click.side_effect = copy
    assert handler._code_export() == 'exported code'
    assert order.mock_calls == [
        call.prepare(), call.copy(EQUIPMENT_CODE_EXPORT, offset=(5, 5), interval=3), call.read(),
    ]


def test_export_failure_does_not_read_clipboard():
    handler = make_handler()
    handler.handle_info_bar = Mock()
    handler.device.ensure_clipboard.return_value = False

    assert handler._code_export() is None
    handler.loop.assert_not_called()
    handler.device.get_clipboard.assert_not_called()


@pytest.mark.parametrize('clicked,info_count', [(True, 0), (False, 1)])
def test_export_requires_its_own_copy_and_completion_before_reading(clicked, info_count):
    handler = make_handler()
    handler.handle_info_bar = Mock()
    handler.info_bar_count = Mock(return_value=info_count)
    handler.appear_then_click.return_value = clicked
    handler.device.ensure_clipboard.return_value = True

    assert handler._code_export() is None
    handler.device.get_clipboard.assert_not_called()


def test_export_lock_timeout_does_not_click_or_read_clipboard():
    handler = make_handler()
    handler.handle_info_bar = Mock()
    handler.device.ensure_clipboard.return_value = True

    with FileLock(input_module._CLIPBOARD_LOCK_FILE, timeout=0):
        assert handler._code_export() is None
    handler.appear_then_click.assert_not_called()
    handler.device.get_clipboard.assert_not_called()


def test_export_rejects_an_empty_clipboard():
    handler = make_handler()
    handler.handle_info_bar = Mock()
    handler.info_bar_count = Mock(side_effect=[0, 1])
    handler.device.ensure_clipboard.return_value = True
    handler.device.get_clipboard.return_value = ''

    assert handler._code_export() is None


def test_failed_export_does_not_save_null_code_or_clear_equipment():
    handler = make_handler()
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
