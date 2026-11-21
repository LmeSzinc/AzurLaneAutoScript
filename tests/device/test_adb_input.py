import shlex
from collections import deque
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from lxml import etree

from module.device.app_control import AppControl
from module.device.control import Control
from module.device.method.adb_input import AdbInput
from module.device.method.utils import RETRY_TRIES
from module.exception import RequestHumanTakeover


TEXTBOX = SimpleNamespace(button=(10, 20, 110, 60))
EMPTY_CLIPBOARD = 'Result: Parcel(00000000 00000000)'


@pytest.fixture(autouse=True)
def no_retry_delay(monkeypatch):
    monkeypatch.setattr('module.device.method.adb.time.sleep', lambda _: None)


def editor(text='', *, focused=True):
    root = etree.Element('hierarchy')
    attrs = {'class': 'android.widget.EditText', 'enabled': 'true', 'focused': str(focused).lower(),
             'password': 'false', 'bounds': '[10,20][110,60]', 'text': text}
    etree.SubElement(root, 'node', attrib=attrs)
    return root


class NativeAdbInput(AdbInput):
    """Small native-only fixture; missing attributes reject u2/IME shortcuts."""

    click = Control.click
    xpath_to_button = AppControl.xpath_to_button

    def __init__(self, *, hierarchies=(), replies=(), sdk_ver=35, user='0',
                 input_method=('mInputShown=false',)):
        self.sdk_ver, self.hierarchies = sdk_ver, deque(hierarchies)
        self.replies, self.user = deque(replies or [EMPTY_CLIPBOARD]), user
        self.config = SimpleNamespace(Emulator_ControlMethod='ADB')
        self.click_methods = {'ADB': self.click_adb}
        self.handle_control_check, self.sleep = Mock(), Mock()
        self.shell_calls, self.events = [], []
        self.input_method = deque(input_method)
        self.fail_token, self.failures = '', 0

    def __getattr__(self, name):
        raise AssertionError(f'ADB backend touched forbidden API: {name}')

    def adb_shell(self, command, timeout=10):
        args = shlex.split(command) if isinstance(command, str) else command
        self.shell_calls.append(args)
        self.events.append(args)
        if self.failures and self.fail_token in ' '.join(map(str, args)):
            self.failures -= 1
            raise OSError('ADB command failed')
        if command == ['dumpsys', 'input_method']:
            return self.input_method.popleft()
        if command == ['am', 'get-current-user']:
            return self.user
        if args[:3] == ['service', 'call', 'clipboard']:
            return self.replies.popleft() if len(self.replies) > 1 else self.replies[0]
        return ''

    def dump_hierarchy_adb(self):
        self.events.append('hierarchy')
        return self.hierarchies.popleft()

    def click_adb(self, x, y):
        self.adb_shell(['input', 'tap', x, y])


def shell_args(device):
    return [command for command in device.shell_calls if command[0] == 'input']


def test_ready_editor_clears_text_and_types_literal_ascii_without_wait():
    text = 'literal space %s 100% ; rm -rf / "$HOME" \'quoted\''
    device = NativeAdbInput(hierarchies=[editor('x' * 260 + '😀')])

    assert device.input_text_adb(text, TEXTBOX) is None
    args = shell_args(device)
    device.handle_control_check.assert_called_once_with(TEXTBOX)
    device.sleep.assert_not_called()
    values = [command[2] for command in args if command[:2] == ['input', 'text']]
    assert ''.join(values) == text
    assert all('%s' not in value for value in values)
    assert args[-1] == ['input', 'keyevent', 'KEYCODE_ENTER']
    assert not any(arg[:2] == ['input', 'keycombination'] for arg in args)
    forward = [arg for arg in args if 'KEYCODE_FORWARD_DEL' in arg]
    backward = [arg for arg in args if 'KEYCODE_DEL' in arg]
    assert [sum(arg.count('KEYCODE_FORWARD_DEL') for arg in forward),
            sum(arg.count('KEYCODE_DEL') for arg in backward)] == [262, 262]
    assert all(len(arg) - 2 <= 128 for arg in forward + backward)


def test_input_waits_for_focus_then_dismisses_keyboard(monkeypatch):
    interval, timeout = Mock(), Mock()
    interval.start.return_value, timeout.start.return_value = interval, timeout
    interval.reached_and_reset.side_effect = [False, True, False, True]
    timeout.reached.return_value = False
    monkeypatch.setattr('module.device.method.adb_input.Timer', lambda limit: interval if limit == 1 else timeout)
    device = NativeAdbInput(
        hierarchies=[editor(focused=False), editor(focused=False), editor('old')],
        input_method=['mInputShown=true', 'mInputShown=true', 'mInputShown=false'],
    )

    device.input_text_adb('code', TEXTBOX)

    assert device.handle_control_check.call_count == 2
    reads = [i for i, event in enumerate(device.events) if event == 'hierarchy']
    assert len(reads) == 3
    assert all(event[:2] == ['input', 'tap'] for event in device.events[:reads[-1]] if isinstance(event, list))
    assert shell_args(device)[-2:] == [
        ['input', 'keyevent', 'KEYCODE_ENTER'], ['input', 'keyevent', 'KEYCODE_BACK'],
    ]
    assert device.sleep.call_count == 2


@pytest.mark.parametrize('text', ['line\nbreak', 'tab\tbreak', '蓝色 code'])
def test_non_ascii_or_control_text_rejects_before_focus(text):
    device = NativeAdbInput()
    with pytest.raises(RequestHumanTakeover):
        device.input_text_adb(text, TEXTBOX)
    device.handle_control_check.assert_not_called()
    assert device.shell_calls == []


def test_persistent_input_failure_requests_takeover():
    device = NativeAdbInput(hierarchies=[editor('old')] * RETRY_TRIES)
    device.fail_token, device.failures = 'input text code', RETRY_TRIES
    with pytest.raises(RequestHumanTakeover):
        device.input_text_adb('code', TEXTBOX)
    assert shell_args(device).count(['input', 'text', 'code']) == RETRY_TRIES


@pytest.mark.parametrize('failed', ['input text s', 'KEYCODE_ENTER'])
def test_input_retry_clears_partial_text_before_replacing_it(failed):
    device = NativeAdbInput(hierarchies=[editor('old'), editor('partial input')])
    device.fail_token, device.failures = failed, 1

    assert device.input_text_adb('code%s', TEXTBOX) is None

    args = shell_args(device)
    first, second = [i for i, command in enumerate(args) if command == ['input', 'text', 'code%']]
    assert any('KEYCODE_DEL' in command for command in args[first:second])


@pytest.mark.parametrize('sdk,transaction,arguments', [
    (24, 2, []), (27, 2, []), (28, 3, []),
    (29, 3, ['i32', '10']), (30, 3, ['i32', '10']),
    (31, 4, ['i32', '10']), (32, 4, ['i32', '10']),
    (33, 4, ['i32', '-1', 'i32', '10']),
    (34, 4, ['i32', '-1', 'i32', '10', 'i32', '0']),
    (35, 4, ['i32', '-1', 'i32', '10', 'i32', '0']),
    (36, 4, ['i32', '-1', 'i32', '10', 'i32', '0']),
])
def test_clipboard_prepares_once_then_reads_without_ui(sdk, transaction, arguments):
    device = NativeAdbInput(sdk_ver=sdk, user='10')
    device.ensure_clipboard_adb()
    assert device.shell_calls == ([['am', 'get-current-user']] if sdk >= 29 else [])
    device.shell_calls.clear()

    assert device.get_clipboard_adb() == ''
    assert device.get_clipboard_adb() == ''

    command = ['service', 'call', 'clipboard', str(transaction), 's16', 'com.android.shell'] + arguments
    assert device.shell_calls == [command, command]
    assert 'hierarchy' not in device.events
    device.handle_control_check.assert_not_called()
    device.sleep.assert_not_called()


@pytest.mark.parametrize('exception', [0, -2, -3])
def test_android13_read_falls_back_once_and_caches_signature(exception):
    fixtures = Path(__file__).with_name('fixtures') / 'adb_clipboard'
    # SDK 31+ share the layout through the first text item.
    replies = [(fixtures / name).read_text() for name in ('android15-unicode.parcel', 'android15-url.parcel')]
    if exception:
        replies.insert(0, f'Result: Parcel({exception & 0xffffffff:08x} 00000000 00000000)')
    device = NativeAdbInput(sdk_ver=33, replies=replies)
    device.ensure_clipboard_adb()
    assert device.shell_calls == [['am', 'get-current-user']]
    device.shell_calls.clear()

    assert device.get_clipboard_adb() == '中文 日本語 café 😀 𠀋'
    assert len(device.shell_calls) == (2 if exception else 1)
    selected = device.shell_calls[-1]
    assert selected == ['service', 'call', 'clipboard', '4', 's16', 'com.android.shell'] + (
        ['i32', '0'] if exception else ['i32', '-1', 'i32', '0'])
    device.shell_calls.clear()

    assert device.get_clipboard_adb() == 'https://example.com/a.b?x=1&y=2'
    assert device.shell_calls == [selected]


@pytest.mark.parametrize('reply', [
    'Result: Parcel(ffffffff 00000000 00000000)', 'Result: Parcel(00000000)',
], ids=['permission-denied', 'truncated'])
def test_invalid_clipboard_retries_without_signature_fallback(reply):
    device = NativeAdbInput(sdk_ver=33, replies=[reply])
    with pytest.raises(RequestHumanTakeover):
        device.get_clipboard_adb()
    reads = [command for command in device.shell_calls if command[0] == 'service']
    assert len(reads) == RETRY_TRIES
    assert all(command == reads[0] for command in reads)


def test_clipboard_retries_a_failed_read_without_ui():
    device = NativeAdbInput()
    device.fail_token, device.failures = 'service call clipboard', 1

    assert device.get_clipboard_adb() == ''
    assert sum(command[0] == 'service' for command in device.shell_calls) == 2
    assert 'hierarchy' not in device.events


@pytest.mark.parametrize('sdk', [23, 37])
def test_unsupported_clipboard_requests_takeover_without_binder_probing(sdk):
    device = NativeAdbInput(sdk_ver=sdk)
    with pytest.raises(RequestHumanTakeover):
        device.get_clipboard_adb()
    assert device.shell_calls == []
