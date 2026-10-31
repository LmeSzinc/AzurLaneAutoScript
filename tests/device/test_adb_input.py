import shlex
from unittest.mock import Mock

import pytest

import module.device.method.adb_input as adb_input_module
from module.device.method.adb_input import AdbInput


MARKER_SUFFIX = '; printf "\\n__ALAS_INPUT_EXIT__%s" "$?"'
SUCCESS = '\n__ALAS_INPUT_EXIT__0'


class FakeDevice:
    def __init__(self, sdk_ver=33, responses=None, keyboard=None):
        self.sdk_ver = sdk_ver
        self.responses = list(responses or [])
        self.keyboard = list(keyboard or [])
        self.shell_calls = []
        self.sleep_calls = []
        self.u2 = Mock()
        self.clear_text_uiautomator2 = Mock(return_value=True)
        self.keyevent_uiautomator2 = Mock(return_value=True)
        self.current_ime = Mock()
        self.get_clipboard = Mock()

    def adb_shell(self, command, timeout=10):
        self.shell_calls.append((command, timeout))
        if self.responses:
            return self.responses.pop(0)
        return SUCCESS

    def sleep(self, seconds):
        self.sleep_calls.append(seconds)

    def is_keyboard_shown(self):
        return self.keyboard.pop(0) if self.keyboard else False


def command_args(call):
    command, timeout = call
    assert timeout == 30
    assert command.endswith(MARKER_SUFFIX)
    return shlex.split(command[:-len(MARKER_SUFFIX)])


@pytest.mark.parametrize('clear,expected_prefix', [
    (True, []),
    (False, [['input', 'keyevent', 'KEYCODE_MOVE_END']]),
])
def test_replace_and_append_use_distinct_selection_sequences(clear, expected_prefix):
    device = FakeDevice()
    focus = Mock()

    assert AdbInput(device).input_text_adb('new code', focus, clear=clear) is True

    args = [command_args(call) for call in device.shell_calls]
    assert args[:len(expected_prefix)] == expected_prefix
    assert all(arg[:2] != ['input', 'keycombination'] for arg in args)
    assert args[len(expected_prefix):-1] == [['input', 'text', 'new code']]
    assert args[-1] == ['input', 'keyevent', 'KEYCODE_ENTER']
    focus.assert_called_once_with()
    device.current_ime.assert_not_called()
    device.get_clipboard.assert_not_called()
    device.u2.assert_not_called()
    if clear:
        device.clear_text_uiautomator2.assert_called_once_with()
    else:
        device.clear_text_uiautomator2.assert_not_called()
    device.keyevent_uiautomator2.assert_not_called()


def test_adb_input_has_no_sdk_shortcut_restriction():
    device = FakeDevice(sdk_ver=30)

    assert AdbInput(device).adb_input_supported() is True
    assert AdbInput(device).ensure_adb_input() is True


def test_native_clear_failure_stops_before_adb_text_input():
    device = FakeDevice()
    device.clear_text_uiautomator2.return_value = False

    assert AdbInput(device).input_text_adb('new code', Mock()) is False

    device.clear_text_uiautomator2.assert_called_once_with()
    assert device.shell_calls == []
    device.keyevent_uiautomator2.assert_not_called()


@pytest.mark.parametrize('text', ['line\nbreak', 'tab\tbreak', '蓝色 code'])
def test_non_printable_or_non_ascii_text_is_rejected_before_clearing(text):
    device = FakeDevice()
    focus = Mock()

    assert AdbInput(device).input_text_adb(text, focus) is False
    assert focus.call_count == 0
    assert device.shell_calls == []


def test_spaces_percent_s_and_shell_metacharacters_are_preserved_as_arguments():
    device = FakeDevice()
    focus = Mock()
    text = 'literal space %s percent%sign 100% ; rm -rf / "$HOME" \'quoted\''

    assert AdbInput(device).input_text_adb(text, focus, clear=False) is True

    args = [command_args(call) for call in device.shell_calls]
    text_args = [arg[2] for arg in args if arg[:2] == ['input', 'text']]
    assert ''.join(text_args) == text
    assert all('%s' not in value for value in text_args)
    assert args[-1] == ['input', 'keyevent', 'KEYCODE_ENTER']
    # Parsing the generated command as the remote POSIX shell would must not
    # turn the text into extra commands or extra arguments.
    assert ['input', 'text', text_args[0]] in args
    assert all(arg[0:2] != ['rm', '-rf'] for arg in args)


@pytest.mark.parametrize('response', ['', '\n__ALAS_INPUT_EXIT__1'])
def test_shell_failure_or_missing_status_marker_stops_the_remaining_sequence(response):
    device = FakeDevice(responses=[response])
    focus = Mock()

    assert AdbInput(device).input_text_adb('code', focus) is False
    assert focus.call_count == 1
    assert len(device.shell_calls) == 1


def test_keyboard_hidden_does_not_receive_a_back_key():
    device = FakeDevice(keyboard=[False])

    assert AdbInput(device).input_text_adb('code', Mock()) is True

    args = [command_args(call) for call in device.shell_calls]
    assert args[-1] == ['input', 'keyevent', 'KEYCODE_ENTER']
    assert ['input', 'keyevent', 'KEYCODE_BACK'] not in args


def test_keyboard_shown_is_dismissed_with_back_and_waits_until_hidden():
    device = FakeDevice(keyboard=[True, True, False])

    assert AdbInput(device).input_text_adb('code', Mock()) is True

    args = [command_args(call) for call in device.shell_calls]
    assert args[-2:] == [
        ['input', 'keyevent', 'KEYCODE_ENTER'],
        ['input', 'keyevent', 'KEYCODE_BACK'],
    ]
    assert device.sleep_calls[-1] == 0.1


def test_keyboard_dismissal_timeout_reports_failure(monkeypatch):
    class ExpiredTimer:
        def __init__(self, _limit):
            pass

        def start(self):
            return self

        def reached(self):
            return True

    monkeypatch.setattr(adb_input_module, 'Timer', ExpiredTimer)
    device = FakeDevice(keyboard=[True, True])

    assert AdbInput(device).input_text_adb('code', Mock()) is False
    args = [command_args(call) for call in device.shell_calls]
    assert args[-1] == ['input', 'keyevent', 'KEYCODE_BACK']

