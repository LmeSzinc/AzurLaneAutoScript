import base64
from types import SimpleNamespace
from unittest.mock import ANY, Mock, call

import pytest
from lxml import etree

import module.device.method.fastinput_ime as fastinput_module
from module.device.control import Control
from module.device.device import Device
from module.device.method.fastinput_ime import FastInputIME
from module.device.method.uiautomator_2 import Uiautomator2


def make_device(sdk_ver=28, mumu_version=None, bluestacks_air=False):
    device = object.__new__(Device)
    device.sdk_ver = sdk_ver
    device.is_mumu_family = mumu_version is not None
    device.nemud_player_version = '' if mumu_version is None else mumu_version
    device.is_bluestacks_air = bluestacks_air
    device.config = SimpleNamespace(Emulator_ControlMethod='minitouch')
    device.u2 = SimpleNamespace(
        current_ime=Mock(side_effect=AssertionError('Legacy uiautomator2 IME query must not be used')),
        shell=Mock(return_value=SimpleNamespace(exit_code=0, output='')),
        send_keys=Mock(), send_action=Mock(), clipboard='exported code',
        dump_hierarchy=Mock(return_value='<hierarchy/>'), click=Mock(),
    )
    device.current_ime_uiautomator2 = Mock(return_value=(FastInputIME.FASTINPUT_IME, False))
    device.adb_shell = Mock(return_value='')
    device.click = Mock()
    device.sleep = Mock()
    device.stuck_record_check = Mock()
    return device


def test_uiautomator2_keyboard_and_clipboard_work_without_fastinput_helper():
    assert not issubclass(Uiautomator2, FastInputIME)
    device = object.__new__(Uiautomator2)
    device.u2 = SimpleNamespace(
        current_ime=Mock(side_effect=AssertionError('Legacy query')),
        clipboard='exported code', shell=Mock(),
    )
    device.adb_shell = Mock(return_value='mSelectedMethodId=stock/.IME\nmInputShown=true')

    assert device.current_ime_uiautomator2() == ('stock/.IME', True)
    assert device.is_keyboard_shown_uiautomator2() is True
    assert device.get_clipboard_uiautomator2() == 'exported code'
    device.u2.shell.assert_not_called()
    device.u2.current_ime.assert_not_called()


@pytest.mark.parametrize('dump,expected', [
    ('mCurMethodId=stock/.IME\nmInputShown=false', ('stock/.IME', False)),
    ('mSelectedMethodId=stock/.IME\nmInputShown=true', ('stock/.IME', True)),
    ('mSelectedMethodId=stock/.IME\nmCurId=other/.IME\nmInputShown=false', ('stock/.IME', False)),
    ('mCurMethodId=stock/.IME\nmCurId=other/.IME\nmInputShown=true', ('stock/.IME', True)),
    ('mSelectedMethodId=stock/.IME\nmCurMethodId=old/.IME', ('stock/.IME', False)),
    ('mSelectedMethodId=null\nmCurId=old/.IME\nmInputShown=false', (None, False)),
    ('mCurId=old/.IME\nmInputShown=false', (None, False)),
    ('', (None, False)),
])
def test_current_ime_accepts_both_dump_formats_without_substituting_the_bound_ime(dump, expected):
    device = object.__new__(Uiautomator2)
    device.adb_shell = Mock(return_value=dump)

    assert device.current_ime_uiautomator2() == expected
    device.adb_shell.assert_called_once_with(['dumpsys', 'input_method'])


@pytest.mark.parametrize('header,expected', [
    ('mCurrentImeUserId=10\n', ('work/.IME', False)),
    ('mCurrentImeUserId=0\n', ('stock/.IME', True)),
    ('mCurrentUserId=10\n', ('work/.IME', False)),
    ('mCurrentUserId=0\nmCurrentImeUserId=10\n', ('work/.IME', False)),
    ('mCurrentImeUserId=20\n', (None, False)),
    ('', (None, False)),
])
def test_current_ime_keeps_selected_ime_and_keyboard_state_in_the_current_user(header, expected):
    device = object.__new__(Uiautomator2)
    device.adb_shell = Mock(return_value=(
        header + '  UserId=0\n    mSelectedMethodId=stock/.IME\n    mInputShown=true\n'
        '  UserId=10\n    mSelectedMethodId=work/.IME\n    mInputShown=false\n'))

    assert device.current_ime_uiautomator2() == expected


def test_current_ime_accepts_a_single_user_dump_without_a_current_user_header():
    device = object.__new__(Uiautomator2)
    device.adb_shell = Mock(return_value='  UserId=10\n    mCurMethodId=work/.IME\n    mInputShown=true\n')

    assert device.current_ime_uiautomator2() == ('work/.IME', True)


def test_input_helpers_use_their_own_devices_current_state():
    first = make_device()
    second = make_device(sdk_ver=33, bluestacks_air=True)
    helper = first.fastinput_ime

    assert helper.device is first
    assert second.fastinput_ime.device is second
    assert helper is not second.fastinput_ime
    first.config.Emulator_ControlMethod = 'ADB'
    assert first.text_input_supported() is False
    assert second.text_input_supported() is True
    first.config.Emulator_ControlMethod = 'MaaTouch'
    assert first.text_input_supported() is True
    second.adb_shell.return_value = '1'

    assert first.ensure_text_input() is True
    assert second.ensure_text_input() is True
    first.adb_shell.assert_not_called()
    second.adb_shell.assert_called_once_with(['settings', 'get', 'secure', 'show_ime_with_hard_keyboard'])


def bounded_timers(monkeypatch, polls=3):
    class PollTimer:
        def __init__(self, *args, **kwargs):
            self.polls = 0

        def start(self):
            return self

        def reset(self):
            return self

        def wait(self):
            pass

        def reached(self):
            self.polls += 1
            return self.polls > polls

        def reached_and_reset(self):
            return True

    monkeypatch.setattr(fastinput_module, 'Timer', PollTimer)


def ime_hierarchy(resource_id, fastinput=False, others=(True, True)):
    hierarchy = etree.Element('hierarchy')
    for index, (name, checked, enabled) in enumerate((
        ('FastInputIME', fastinput, True),
        ('Stock A', others[0], True),
        ('Stock B', others[1], True),
        ('Fixed keyboard', True, False),
    )):
        row = etree.SubElement(hierarchy, 'node')
        etree.SubElement(row, 'node', attrib={'resource-id': 'android:id/title', 'text': name})
        etree.SubElement(row, 'node', attrib={
            'resource-id': resource_id, 'checked': str(checked).lower(),
            'enabled': str(enabled).lower(), 'bounds': f'[10,{20 + 50 * index}][30,{40 + 50 * index}]',
        })
    return hierarchy


@pytest.mark.parametrize('method,supported', [
    ('uiautomator2', True), ('minitouch', True), ('MaaTouch', True),
    ('ADB', False), ('Hermit', False), ('scrcpy', False), ('nemu_ipc', False),
])
def test_text_input_keeps_existing_control_method_support(method, supported):
    device = make_device()
    device.config.Emulator_ControlMethod = method

    assert device.text_input_supported() is supported


@pytest.mark.parametrize('sdk,mumu_version,air,resource_id', [
    (28, None, False, 'android:id/switch_widget'),
    (32, '3.8.27.2950', False, 'android:id/switch_widget'),
    (32, '', False, 'android:id/switch_widget'),
    (35, '', False, 'com.android.settings:id/switchWidget'),
    (35, None, False, 'com.android.settings:id/switchWidget'),
    (28, None, False, 'com.android.settings:id/switchWidget'),
    (35, None, False, 'android:id/switch_widget'),
    (33, None, True, 'android:id/switch_widget'),
])
def test_settings_enable_confirm_and_disable_each_competing_ime(sdk, mumu_version, air, resource_id):
    device = make_device(sdk_ver=sdk, mumu_version=mumu_version, bluestacks_air=air)
    confirmation = etree.fromstring(
        '<hierarchy><node resource-id="android:id/button1" bounds="[100,100][120,120]"/></hierarchy>')
    frames = iter([
        ime_hierarchy(resource_id), confirmation,
        ime_hierarchy(resource_id, True),
        ime_hierarchy(resource_id, True, (False, True)),
        ime_hierarchy(resource_id, True, (False, False)),
    ])
    device.u2.dump_hierarchy.side_effect = lambda **kwargs: etree.tostring(next(frames)).decode('utf-8')

    assert device.fastinput_ime._enable_fastinput_ime() is True

    assert [args[0][0].button for args in device.click.call_args_list] == [
        (10, 20, 30, 40), (100, 100, 120, 120), (10, 70, 30, 90), (10, 120, 30, 140),
    ]
    assert device.u2.dump_hierarchy.call_count == 5
    device.u2.dump_hierarchy.assert_called_with(compressed=False)
    device.u2.click.assert_not_called()
    assert device.adb_shell.call_args_list == [
        call(['am', 'start', '-a', 'android.settings.INPUT_METHOD_SETTINGS']),
        call(['input', 'keyevent', '4']),
    ]


@pytest.mark.parametrize('method', ['uiautomator2', 'minitouch', 'MaaTouch'])
def test_settings_clicks_use_configured_controller_and_device_checks(method):
    device = make_device()
    device.config.Emulator_ControlMethod = method
    device.click = Control.click.__get__(device, Device)
    device.handle_control_check = Mock()
    controllers = {
        'uiautomator2': Mock(), 'minitouch': Mock(), 'MaaTouch': Mock(),
    }
    device.click_uiautomator2 = controllers['uiautomator2']
    device.click_minitouch = controllers['minitouch']
    device.click_maatouch = controllers['MaaTouch']
    device.u2.dump_hierarchy.side_effect = [
        etree.tostring(ime_hierarchy('android:id/switch_widget', others=(False, False))).decode('utf-8'),
        etree.tostring(ime_hierarchy('android:id/switch_widget', True, (False, False))).decode('utf-8'),
    ]

    assert device.fastinput_ime._enable_fastinput_ime() is True
    device.handle_control_check.assert_called_once()
    assert device.handle_control_check.call_args[0][0].button == (10, 20, 30, 40)
    controllers[method].assert_called_once()
    x, y = controllers[method].call_args[0]
    assert 10 <= x <= 30 and 20 <= y <= 40
    for name, controller in controllers.items():
        if name != method:
            controller.assert_not_called()


def test_settings_navigation_resets_stuck_detection_during_intentional_app_switch():
    device = make_device()
    device.stuck_record_check = Device.stuck_record_check.__get__(device, Device)
    device.app_is_running = Mock(return_value=False)
    for name in ('stuck_timer', 'stuck_timer_long'):
        reached = Mock(return_value=True)
        reset = Mock(side_effect=lambda timer=reached: setattr(timer, 'return_value', False))
        setattr(device, name, SimpleNamespace(reached=reached, reset=reset))
    device.u2.dump_hierarchy.return_value = etree.tostring(
        ime_hierarchy('android:id/switch_widget', True, (False, False))).decode('utf-8')

    assert device.fastinput_ime._enable_fastinput_ime() is True
    device.app_is_running.assert_not_called()
    assert device.stuck_timer.reset.call_count == 2
    assert device.stuck_timer_long.reset.call_count == 2


@pytest.mark.parametrize('sdk,mumu_version,expected_bounds', [
    (32, '3.8.27.2950', (10, 20, 30, 40)),
    (32, '', (200, 20, 220, 40)),
    (35, None, (200, 20, 220, 40)),
])
def test_connection_flags_choose_first_switch_when_both_layouts_are_present(
        monkeypatch, sdk, mumu_version, expected_bounds):
    device = make_device(sdk_ver=sdk, mumu_version=mumu_version)
    bounded_timers(monkeypatch, polls=1)
    hierarchy = ime_hierarchy('android:id/switch_widget', others=(False, False))
    modern = ime_hierarchy('com.android.settings:id/switchWidget')
    modern[0][1].set('bounds', '[200,20][220,40]')
    hierarchy.append(modern[0])
    device.u2.dump_hierarchy.return_value = etree.tostring(hierarchy).decode('utf-8')

    assert device.fastinput_ime._enable_fastinput_ime() is False
    device.click.assert_called_once()
    assert device.click.call_args[0][0].button == expected_bounds
    device.u2.click.assert_not_called()


@pytest.mark.parametrize('missing_fastinput', [False, True])
def test_settings_timeout_returns_to_game_without_disabling_unrelated_imes(monkeypatch, missing_fastinput):
    device = make_device()
    bounded_timers(monkeypatch)
    hierarchy = ime_hierarchy('android:id/switch_widget' if missing_fastinput else 'unknown:switch')
    if missing_fastinput:
        hierarchy.remove(hierarchy[0])
    device.u2.dump_hierarchy.return_value = etree.tostring(hierarchy).decode('utf-8')

    assert device.fastinput_ime._enable_fastinput_ime() is False
    assert device.u2.dump_hierarchy.call_count == 3
    device.u2.click.assert_not_called()
    device.click.assert_not_called()
    assert device.adb_shell.call_args_list[-1] == call(['input', 'keyevent', '4'])


def test_settings_returns_to_game_if_hierarchy_fails():
    device = make_device()
    device.dump_hierarchy = Mock(side_effect=RuntimeError('hierarchy unavailable'))

    with pytest.raises(RuntimeError, match='hierarchy unavailable'):
        device.fastinput_ime._enable_fastinput_ime()
    assert device.adb_shell.call_args_list[-1] == call(['input', 'keyevent', '4'])


@pytest.mark.parametrize('dialog', [False, True])
def test_settings_timeout_also_applies_when_clicks_do_not_change_the_page(monkeypatch, dialog):
    device = make_device()
    bounded_timers(monkeypatch)
    if dialog:
        hierarchy = etree.fromstring(
            '<hierarchy><node resource-id="android:id/button1" bounds="[100,100][120,120]"/></hierarchy>')
    else:
        hierarchy = ime_hierarchy('android:id/switch_widget')
    device.u2.dump_hierarchy.return_value = etree.tostring(hierarchy).decode('utf-8')

    assert device.fastinput_ime._enable_fastinput_ime() is False
    assert device.click.call_count == 3
    assert device.adb_shell.call_args_list[-1] == call(['input', 'keyevent', '4'])


def test_selected_ime_does_not_run_shell_setup():
    device = make_device()

    assert device.ensure_text_input() is True
    device.u2.shell.assert_not_called()
    device.adb_shell.assert_not_called()


def test_shell_setup_checks_effective_ime():
    device = make_device()
    selected = ['stock/.IME']
    device.current_ime_uiautomator2.side_effect = lambda: (selected[0], False)

    def shell(command):
        if command[1] == 'set':
            selected[0] = FastInputIME.FASTINPUT_IME
        return SimpleNamespace(exit_code=0, output='OK')

    device.u2.shell.side_effect = shell
    device.fastinput_ime._enable_fastinput_ime = Mock()

    assert device.ensure_text_input() is True
    assert device.u2.shell.call_args_list == [
        call(['ime', 'enable', FastInputIME.FASTINPUT_IME]), call(['ime', 'set', FastInputIME.FASTINPUT_IME]),
    ]
    device.fastinput_ime._enable_fastinput_ime.assert_not_called()


@pytest.mark.parametrize('result', [
    SimpleNamespace(exit_code=1, output='command disabled'),
    RuntimeError('shell unavailable'),
])
def test_failed_shell_uses_settings_fallback(result):
    device = make_device()
    selected = ['stock/.IME']
    device.current_ime_uiautomator2.side_effect = lambda: (selected[0], False)
    if isinstance(result, Exception):
        device.u2.shell.side_effect = result
    else:
        device.u2.shell.return_value = result

    def enable():
        selected[0] = FastInputIME.FASTINPUT_IME
        return True

    device.fastinput_ime._enable_fastinput_ime = Mock(side_effect=enable)

    assert device.ensure_text_input() is True
    device.fastinput_ime._enable_fastinput_ime.assert_called_once_with()


def test_settings_switches_and_successful_shell_do_not_prove_ime_selection():
    device = make_device(sdk_ver=35, mumu_version='')
    device.current_ime_uiautomator2.return_value = ('stock/.IME', False)
    device.fastinput_ime._enable_fastinput_ime = Mock(return_value=True)

    assert device.ensure_text_input() is False
    device.fastinput_ime._enable_fastinput_ime.assert_called_once_with()


def test_bluestacks_prepares_onscreen_keyboard_even_when_fastinput_is_selected():
    device = make_device(sdk_ver=33, bluestacks_air=True)
    value = ['0']

    def shell(command):
        if command[1] == 'put':
            value[0] = command[-1]
            return ''
        return value[0]

    device.adb_shell.side_effect = shell

    assert device.ensure_text_input() is True
    assert device.adb_shell.call_args_list == [
        call(['settings', 'get', 'secure', 'show_ime_with_hard_keyboard']),
        call(['settings', 'put', 'secure', 'show_ime_with_hard_keyboard', '1']),
        call(['settings', 'get', 'secure', 'show_ime_with_hard_keyboard']),
    ]
    device.u2.shell.assert_not_called()


def test_bluestacks_setting_failure_keeps_input_available_and_reports_manual_setting(monkeypatch):
    device = make_device(sdk_ver=33, bluestacks_air=True)
    device.adb_shell.return_value = '0'
    warning = Mock()
    monkeypatch.setattr(fastinput_module.logger, 'warning', warning)

    assert device.ensure_text_input() is True
    warning.assert_called_with('Enable the on-screen keyboard in BlueStacks Air input settings.')


@pytest.mark.parametrize('already_shown', [False, True])
def test_input_focuses_target_before_sending_even_with_stale_keyboard_state(already_shown):
    device = make_device()
    shown = [already_shown]
    device.current_ime_uiautomator2.side_effect = lambda: (FastInputIME.FASTINPUT_IME, shown[0])
    button = object()

    def focus(target):
        assert target is button
        shown[0] = True

    def shell(command):
        device.click.assert_called_once_with(button)
        return SimpleNamespace(exit_code=0, output='Broadcast completed')

    device.click.side_effect = focus
    device.u2.shell.side_effect = shell

    assert device.input_text('R0o4LzAvMC80SU9ML1FMXDA=', button) is True
    assert device.u2.shell.call_args_list == [
        call(['am', 'broadcast', '-a', 'ADB_SET_TEXT', '--es', 'text',
              base64.b64encode(b'R0o4LzAvMC80SU9ML1FMXDA=').decode('ascii')]),
        call(['am', 'broadcast', '-a', 'ADB_EDITOR_CODE', '--ei', 'code', '6']),
    ]
    device.u2.send_keys.assert_not_called()
    device.u2.send_action.assert_not_called()
    device.u2.current_ime.assert_not_called()


@pytest.mark.parametrize('clear,action', [(True, 'ADB_SET_TEXT'), (False, 'ADB_INPUT_TEXT')])
def test_fastinput_broadcast_preserves_utf8_and_clear_mode(clear, action):
    device = make_device()
    device.current_ime_uiautomator2.return_value = (FastInputIME.FASTINPUT_IME, True)
    text = '蓝 Aa09+/= "\n'

    assert device.input_text(text, object(), clear=clear) is True

    command = device.u2.shell.call_args_list[0][0][0]
    assert command[:-1] == ['am', 'broadcast', '-a', action, '--es', 'text']
    assert base64.b64decode(command[-1]).decode('utf-8') == text
    device.u2.send_keys.assert_not_called()
    device.u2.send_action.assert_not_called()
    device.u2.current_ime.assert_not_called()


@pytest.mark.parametrize('failed_command', [0, 1])
@pytest.mark.parametrize('output', ['broadcast denied', None])
def test_fastinput_does_not_report_success_after_a_failed_broadcast(failed_command, output):
    device = make_device()
    device.current_ime_uiautomator2.return_value = (FastInputIME.FASTINPUT_IME, True)
    device.u2.shell.side_effect = [SimpleNamespace(exit_code=0, output='Broadcast completed')] * failed_command + [
        SimpleNamespace(exit_code=1, output=output)]

    assert device.input_text('Aa09+/=', object()) is False
    assert device.u2.shell.call_count == failed_command + 1


@pytest.mark.parametrize('selected_field', ['mCurMethodId', 'mSelectedMethodId'])
def test_fastinput_setup_and_send_use_the_device_parser_throughout(selected_field):
    device = make_device()
    del device.current_ime_uiautomator2
    selected = ['stock/.IME']
    shown = [False]
    device.adb_shell.side_effect = lambda command: (
        f'{selected_field}={selected[0]}\nmInputShown={str(shown[0]).lower()}')

    def shell(command):
        if command[:2] == ['ime', 'set']:
            selected[0] = FastInputIME.FASTINPUT_IME
        return SimpleNamespace(exit_code=0, output='OK')

    device.u2.shell.side_effect = shell
    device.click.side_effect = lambda button: shown.__setitem__(0, True)
    device.fastinput_ime._enable_fastinput_ime = Mock(side_effect=AssertionError('Unnecessary Settings fallback'))

    assert device.input_text('Aa09+/=', object()) is True
    assert device.u2.shell.call_args_list[:2] == [
        call(['ime', 'enable', FastInputIME.FASTINPUT_IME]), call(['ime', 'set', FastInputIME.FASTINPUT_IME]),
    ]
    assert device.u2.shell.call_args_list[2:] == [
        call(['am', 'broadcast', '-a', 'ADB_SET_TEXT', '--es', 'text', 'QWEwOSsvPQ==']),
        call(['am', 'broadcast', '-a', 'ADB_EDITOR_CODE', '--ei', 'code', '6']),
    ]
    device.u2.current_ime.assert_not_called()
    device.u2.send_keys.assert_not_called()
    device.u2.send_action.assert_not_called()


def test_keyboard_timeout_does_not_send_text(monkeypatch):
    device = make_device()
    bounded_timers(monkeypatch)

    assert device.input_text('code', object()) is False
    device.u2.shell.assert_not_called()
    device.u2.send_keys.assert_not_called()
    device.u2.send_action.assert_not_called()


def test_input_failure_does_not_click_game_while_ime_setup_failed():
    device = make_device()
    device.fastinput_ime.ensure_fastinput_ime = Mock(return_value=False)

    assert device.input_text('code', object()) is False
    device.click.assert_not_called()
    device.u2.send_keys.assert_not_called()


def test_clipboard_and_keyboard_facade():
    device = make_device()
    device.current_ime_uiautomator2.return_value = (FastInputIME.FASTINPUT_IME, True)

    assert device.current_ime() == (FastInputIME.FASTINPUT_IME, True)
    assert device.is_keyboard_shown() is True
    assert device.get_clipboard() == 'exported code'


@pytest.mark.parametrize('method', ['', 'uiautomator2', 'FastInputIME', 'unknown backend'])
def test_default_and_unknown_input_methods_use_uiautomator2(method):
    device = make_device()
    device.input_method_override = method
    device.fastinput_ime.ensure_fastinput_ime = Mock(return_value=True)
    device.fastinput_ime.input_text_fastinput_ime = Mock(return_value=False)
    button = object()

    assert device.text_input_supported() is True
    assert device.ensure_text_input() is True
    assert device.input_text('code', button, clear=False) is False
    assert device.is_keyboard_shown() is False
    assert device.get_clipboard() == 'exported code'
    device.fastinput_ime.input_text_fastinput_ime.assert_called_once_with('code', focus=ANY, clear=False)


def test_input_override_only_selects_text_operations():
    device = make_device()
    backend = {
        'supported': Mock(return_value=True),
        'prepare': Mock(return_value=False),
        'input': Mock(return_value=True),
    }
    device.input_methods['OtherIME'] = backend
    device.input_method_override = 'OtherIME'
    button = object()

    assert device.text_input_supported() is True
    assert device.ensure_text_input() is False
    assert device.input_text('code', button, clear=False) is True
    assert device.current_ime() == (FastInputIME.FASTINPUT_IME, False)
    assert device.is_keyboard_shown() is False
    assert device.get_clipboard() == 'exported code'
    backend['input'].assert_called_once_with('code', focus=ANY, clear=False)
    for operation in ('supported', 'prepare'):
        backend[operation].assert_called_once_with()
    device.u2.current_ime.assert_not_called()
    device.u2.send_keys.assert_not_called()
    device.adb_shell.assert_not_called()


def test_clipboard_access_before_android_10_does_not_prepare_an_ime():
    device = make_device(sdk_ver=28)
    device.fastinput_ime.ensure_fastinput_ime = Mock(return_value=False)

    assert device.ensure_clipboard() is True
    device.fastinput_ime.ensure_fastinput_ime.assert_not_called()
