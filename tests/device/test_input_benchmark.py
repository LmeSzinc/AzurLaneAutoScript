from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest
from lxml import etree

import module.daemon.benchmark as benchmark_module
from module.daemon.benchmark import InputBenchmark
from module.exception import RequestHumanTakeover


def make_benchmark_device():
    device = Mock()
    device.sdk_ver = 35
    device.u2 = Mock()
    device.u2.info = {}
    device.adb_shell = Mock(return_value='stock/.IME')
    device._foreground_task_uiautomator2 = Mock(return_value=42)
    device.current_ime = Mock(return_value=('stock/.IME', False))
    device.sleep = Mock()
    device.stuck_record_clear = Mock()
    device.clipboard_copy = Mock()
    device.get_clipboard = Mock()

    def shell(command, *args, **kwargs):
        if isinstance(command, (list, tuple)) and command[:2] == ['pm', 'path']:
            return 'package:/data/app/com.github.uiautomator/base.apk'
        if isinstance(command, (list, tuple)) and command[:3] == ['settings', 'get', 'secure']:
            return 'stock/.IME'
        return ''

    device.adb_shell.side_effect = shell
    device.install_uiautomator2 = Mock()
    return device


def make_backend(supported=True, prepared=True):
    return {
        'supported': Mock(return_value=supported),
        'prepare': Mock(return_value=prepared),
        'input': Mock(),
    }


def make_running_benchmark(device, trial):
    adb = make_backend()
    fast = make_backend()
    device.input_methods = {'ADB': adb, 'FastInputIME': fast}
    benchmark = InputBenchmark(device)
    benchmark._open_textbox = Mock()
    benchmark._clear_textbox = Mock()
    benchmark._trial = Mock(side_effect=trial)
    return benchmark, adb, fast


def shell_text(command):
    if isinstance(command, (list, tuple)):
        return ' '.join(str(value) for value in command)
    return str(command)


def test_input_scene_runs_input_benchmark_without_campaign_or_screenshot_click_setup():
    benchmark = object.__new__(benchmark_module.Benchmark)
    benchmark.config = SimpleNamespace(Benchmark_TestScene='input')
    benchmark.run_simple_input_benchmark = Mock(return_value='ADB')
    benchmark.ensure_campaign_ui = Mock()
    benchmark.uninstall_minicap = Mock()
    benchmark.benchmark = Mock()

    benchmark.run()

    benchmark.run_simple_input_benchmark.assert_called_once_with()
    benchmark.ensure_campaign_ui.assert_not_called()
    benchmark.uninstall_minicap.assert_not_called()
    benchmark.benchmark.assert_not_called()


def test_benchmark_uses_median_trials_and_excludes_preparation_time(monkeypatch):
    device = make_benchmark_device()
    adb = make_backend()
    fast = make_backend()
    device.input_methods = {'ADB': adb, 'FastInputIME': fast}
    samples = {
        adb['input']: iter([0.0, 0.3, 0.1, 0.2]),
        fast['input']: iter([0.0, 0.4, 0.4, 0.4]),
    }
    benchmark = InputBenchmark(device)
    benchmark._open_textbox = Mock()
    benchmark._clear_textbox = Mock()
    benchmark._trial = Mock(side_effect=lambda method: next(samples[method]))
    monkeypatch.setattr(benchmark_module.time, 'perf_counter', Mock(side_effect=[0, 100, 100, 101]))

    assert benchmark.run() == 'ADB'
    assert benchmark.results == {'ADB': 0.2, 'FastInputIME': 0.4}
    assert benchmark.preparation == {'ADB': 100, 'FastInputIME': 1}
    adb['prepare'].assert_called_once_with()
    fast['prepare'].assert_called_once_with()

    device.clipboard_copy.assert_not_called()
    device.get_clipboard.assert_not_called()
    assert not any(
        token in shell_text(record.args[0]).lower()
        for record in device.adb_shell.call_args_list
        for token in ('clipboard', 'paste', 'keycombination', 'ctrl')
    )


def test_benchmark_keeps_testing_fastinput_when_adb_fails():
    device = make_benchmark_device()

    def trial(method):
        if method is device.input_methods['ADB']['input']:
            raise RuntimeError('ADB produced the wrong textbox value')
        return 0.2

    benchmark, adb, fast = make_running_benchmark(device, trial)
    assert benchmark.run() == 'FastInputIME'
    assert 'ADB' in benchmark.failures
    assert benchmark.results == {'FastInputIME': 0.2}
    assert benchmark._clear_textbox.call_count == 2
    assert call(['am', 'task', 'focus', '42'], timeout=15) in device.adb_shell.call_args_list


def textbox_hierarchy(text):
    return etree.fromstring(
        '<hierarchy><node enabled="true" password="false" '
        f'class="android.widget.EditText" text="{text}" bounds="[1,2][30,40]"/>'
        '</hierarchy>')


def make_trial_device(hierarchies):
    device = SimpleNamespace()
    device.dump_hierarchy_uiautomator2 = Mock(side_effect=hierarchies)
    device.click = Mock()
    device.u2 = Mock()
    device.u2.return_value.set_text.return_value = True
    return device


def make_cleanup_device(initial_text, final_text, clear_result=True):
    device = SimpleNamespace()
    device.dump_hierarchy_uiautomator2 = Mock(
        side_effect=[textbox_hierarchy(initial_text), textbox_hierarchy(final_text)])
    device.click = Mock()
    device.u2 = Mock()
    device.u2.return_value.clear_text.return_value = clear_result
    device.adb_shell = Mock()
    return device


def test_clear_textbox_accepts_an_empty_editor_hint():
    device = make_cleanup_device('StaleInput42', 'Search settings')
    benchmark = InputBenchmark(device)

    benchmark._clear_textbox()

    device.u2.return_value.clear_text.assert_called_once_with()
    device.adb_shell.assert_called_once_with(['input', 'keyevent', 'KEYCODE_BACK'])


@pytest.mark.parametrize('final_text,clear_result', [
    (InputBenchmark.TEST_TEXT, True), ('', False),
])
def test_clear_textbox_rejects_retained_sample_or_failed_native_clear(final_text, clear_result):
    device = make_cleanup_device('StaleInput42', final_text, clear_result=clear_result)
    benchmark = InputBenchmark(device)

    with pytest.raises(RuntimeError, match='Cannot clear'):
        benchmark._clear_textbox()
    device.adb_shell.assert_not_called()


def test_textbox_selector_skips_invisible_editors():
    hidden = etree.fromstring(
        '<hierarchy><node enabled="true" visible-to-user="false" password="false" '
        'class="android.widget.EditText" text="hidden" bounds="[1,2][30,40]"/></hierarchy>')
    device = SimpleNamespace(dump_hierarchy_uiautomator2=Mock(return_value=hidden))
    benchmark = InputBenchmark(device)

    with pytest.raises(RuntimeError, match='textbox is no longer available'):
        benchmark._textbox()


@pytest.mark.parametrize('missing', [None, 'com.github.uiautomator', 'com.github.uiautomator.test'])
def test_uiautomator_prerequisite_install_is_only_used_for_missing_apks(missing):
    device = make_benchmark_device()

    def shell(command, *args, **kwargs):
        if isinstance(command, (list, tuple)) and command[:2] == ['pm', 'path']:
            return '' if command[2] == missing else 'package:/data/app/helper/base.apk'
        return 'stock/.IME'

    device.adb_shell.side_effect = shell
    InputBenchmark(device)._prepare_uiautomator()
    if missing is None:
        device.install_uiautomator2.assert_not_called()
    else:
        device.install_uiautomator2.assert_called_once_with()


@pytest.mark.parametrize('failure', ['unsupported', 'prepare'])
def test_backend_failure_before_opening_textbox_does_not_clear_an_editor(failure):
    device = make_benchmark_device()
    benchmark, adb, fast = make_running_benchmark(device, Mock(return_value=0.2))
    if failure == 'unsupported':
        adb['supported'].return_value = False
        fast['supported'].return_value = False
    else:
        adb['prepare'].return_value = False
        fast['prepare'].return_value = False

    with pytest.raises(RequestHumanTakeover, match='No input method passed'):
        benchmark.run()
    benchmark._open_textbox.assert_not_called()
    benchmark._clear_textbox.assert_not_called()


def test_trial_rejects_a_backend_that_reports_false():
    device = make_trial_device([textbox_hierarchy(''), textbox_hierarchy('StaleInput42')])
    benchmark = InputBenchmark(device)

    with pytest.raises(RuntimeError, match='did not replace'):
        benchmark._trial(Mock(return_value=False))


def test_trial_rejects_a_backend_that_reports_success_for_the_wrong_text():
    device = make_trial_device([
        textbox_hierarchy(''), textbox_hierarchy('StaleInput42'), textbox_hierarchy('different result')])
    benchmark = InputBenchmark(device)

    with pytest.raises(RuntimeError, match='did not replace'):
        benchmark._trial(Mock(return_value=True))


def test_benchmark_restores_ime_and_task_after_all_backends_fail():
    device = make_benchmark_device()
    benchmark, _, _ = make_running_benchmark(device, Mock(side_effect=RuntimeError('input failed')))
    restore_ime = Mock()
    restore_task = Mock()
    benchmark._restore_ime = restore_ime
    benchmark._restore_task = restore_task

    with pytest.raises(RequestHumanTakeover, match='No input method passed'):
        benchmark.run()
    restore_ime.assert_called_once()
    restore_task.assert_called_once_with(42)
    device.stuck_record_clear.assert_called_once_with()


def test_benchmark_attempts_task_cleanup_when_ime_cleanup_fails():
    device = make_benchmark_device()
    benchmark, _, _ = make_running_benchmark(device, Mock(side_effect=RuntimeError('input failed')))
    benchmark._restore_ime = Mock(side_effect=RuntimeError('IME restore failed'))
    benchmark._restore_task = Mock(side_effect=RuntimeError('task restore failed'))

    with pytest.raises(RuntimeError, match='restore failed'):
        benchmark.run()
    benchmark._restore_ime.assert_called_once()
    benchmark._restore_task.assert_called_once_with(42)
