import shlex
import statistics
import time
import typing as t

import numpy as np
from rich.table import Table
from rich.text import Text

from module.base.utils import float2str as float2str_
from module.base.utils import random_rectangle_point
from module.campaign.campaign_ui import CampaignUI
from module.daemon.daemon_base import DaemonBase
from module.device.method.utils import HierarchyButton
from module.exception import RequestHumanTakeover
from module.logger import logger


def float2str(n, decimal=3):
    if not isinstance(n, (float, int)):
        return str(n)
    else:
        return float2str_(n, decimal=decimal) + 's'


class Benchmark(DaemonBase, CampaignUI):
    TEST_TOTAL = 15
    TEST_BEST = int(TEST_TOTAL * 0.8)

    def benchmark_test(self, func, *args, **kwargs):
        """
        Args:
            func: Function to test.
            *args: Passes to func.
            **kwargs: Passes to func.

        Returns:
            float: Time cost on average.
        """
        logger.hr(f'Benchmark test', level=2)
        logger.info(f'Testing function: {func.__name__}')
        record = []

        for n in range(1, self.TEST_TOTAL + 1):
            start = time.perf_counter()

            try:
                func(*args, **kwargs)
            except RequestHumanTakeover:
                logger.critical('RequestHumanTakeover')
                logger.warning(f'Benchmark tests failed on func: {func.__name__}')
                return 'Failed'
            except Exception as e:
                logger.exception(e)
                logger.warning(f'Benchmark tests failed on func: {func.__name__}')
                return 'Failed'

            cost = time.perf_counter() - start
            logger.attr(
                f'{str(n).rjust(2, "0")}/{self.TEST_TOTAL}',
                f'{float2str(cost)}'
            )
            record.append(cost)

        logger.info('Benchmark tests done')
        average = float(np.mean(np.sort(record)[:self.TEST_BEST]))
        logger.info(f'Time cost {float2str(average)} ({self.TEST_BEST} best results out of {self.TEST_TOTAL} tests)')
        return average

    @staticmethod
    def evaluate_screenshot(cost):
        if not isinstance(cost, (float, int)):
            return Text(cost, style="bold bright_red")

        if cost < 0.025:
            return Text('Insane Fast', style="bold bright_green")
        if cost < 0.100:
            return Text('Ultra Fast', style="bold bright_green")
        if cost < 0.200:
            return Text('Very Fast', style="bright_green")
        if cost < 0.300:
            return Text('Fast', style="green")
        if cost < 0.500:
            return Text('Medium', style="yellow")
        if cost < 0.750:
            return Text('Slow', style="red")
        if cost < 1.000:
            return Text('Very Slow', style="bright_red")
        return Text('Ultra Slow', style="bold bright_red")

    @staticmethod
    def evaluate_click(cost):
        if not isinstance(cost, (float, int)):
            return Text(cost, style="bold bright_red")

        if cost < 0.100:
            return Text('Fast', style="bright_green")
        if cost < 0.200:
            return Text('Medium', style="yellow")
        if cost < 0.400:
            return Text('Slow', style="red")
        return Text('Very Slow', style="bright_red")

    @staticmethod
    def show(test, data, evaluate_func):
        """
        +--------------+--------+--------+
        |  Screenshot  |  time  | Speed  |
        +--------------+--------+--------+
        |     ADB      | 0.319s |  Fast  |
        | uiautomator2 | 0.476s | Medium |
        |  aScreenCap  | Failed | Failed |
        +--------------+--------+--------+
        """
        # table = PrettyTable()
        # table.field_names = [test, 'Time', 'Speed']
        # for row in data:
        #     table.add_row([row[0], f'{float2str(row[1])}', evaluate_func(row[1])])

        # for row in table.get_string().split('\n'):
        #     logger.info(row)
        table = Table(show_lines=True)
        table.add_column(
            test, header_style="bright_cyan", style="cyan", no_wrap=True
        )
        table.add_column("Time", style="magenta")
        table.add_column("Speed", style="green")
        for row in data:
            table.add_row(
                row[0],
                float2str(row[1]),
                evaluate_func(row[1]),
            )
        logger.print(table, justify='center')

    def benchmark(self, screenshot: t.Tuple[str] = (), click: t.Tuple[str] = ()):
        logger.hr('Benchmark', level=1)
        logger.info(f'Testing screenshot methods: {screenshot}')
        logger.info(f'Testing click methods: {click}')

        screenshot_result = []
        for method in screenshot:
            result = self.benchmark_test(self.device.screenshot_methods[method])
            screenshot_result.append([method, result])

        area = (124, 4, 649, 106)  # Somewhere safe to click.
        click_result = []
        for method in click:
            x, y = random_rectangle_point(area)
            result = self.benchmark_test(self.device.click_methods[method], x, y)
            click_result.append([method, result])

        def compare(res):
            res = res[1]
            if not isinstance(res, (int, float)):
                return 100
            else:
                return res

        logger.hr('Benchmark Results', level=1)
        fastest_screenshot = 'ADB_nc'
        fastest_click = 'minitouch'
        if screenshot_result:
            self.show(test='Screenshot', data=screenshot_result, evaluate_func=self.evaluate_screenshot)
            fastest = sorted(screenshot_result, key=lambda item: compare(item))[0]
            logger.info(f'Recommend screenshot method: {fastest[0]} ({float2str(fastest[1])})')
            fastest_screenshot = fastest[0]
        if click_result:
            self.show(test='Control', data=click_result, evaluate_func=self.evaluate_click)
            fastest = sorted(click_result, key=lambda item: compare(item))[0]
            # Prefer MaaTouch if both minitouch and MaaTouch are fastest
            if 'MaaTouch' in click and fastest[0] == 'minitouch':
                fastest[0] = 'MaaTouch'
            logger.info(f'Recommend control method: {fastest[0]} ({float2str(fastest[1])})')
            fastest_click = fastest[0]

        return fastest_screenshot, fastest_click

    def get_test_methods(self) -> t.Tuple[t.Tuple[str], t.Tuple[str]]:
        device = self.config.Benchmark_DeviceType
        # device == 'emulator'
        screenshot = ['ADB', 'ADB_nc', 'uiautomator2', 'aScreenCap', 'aScreenCap_nc', 'DroidCast', 'DroidCast_raw']
        click = ['ADB', 'uiautomator2', 'minitouch', 'MaaTouch']

        def remove(*args):
            return [l for l in screenshot if l not in args]

        # No ascreencap on Android > 9
        sdk = self.device.sdk_ver
        logger.info(f'sdk_ver: {sdk}')
        if not (21 <= sdk <= 28):
            screenshot = remove('aScreenCap', 'aScreenCap_nc')
        # No nc loopback
        if device in ['plone_cloud_with_adb']:
            screenshot = remove('ADB_nc', 'aScreenCap_nc')
        # VMOS
        if device == 'android_phone_vmos':
            screenshot = ['ADB', 'aScreenCap', 'DroidCast', 'DroidCast_raw']
            click = ['ADB', 'Hermit', 'MaaTouch']
        # Droidcast on SDK 23 (Android 6.0) to SDK 32 (Android 12)
        if not (23 <= sdk <= 32):
            screenshot = remove('DroidCast', 'DroidCast_raw')

        if self.device.nemu_ipc_available():
            screenshot.append('nemu_ipc')
        if self.device.ldopengl_available():
            screenshot.append('ldopengl')
        if self.device.is_bluestacks_air:
            screenshot = [l for l in screenshot if 'DroidCast' not in l]

        scene = self.config.Benchmark_TestScene
        if 'screenshot' not in scene:
            screenshot = []
        if 'click' not in scene:
            click = []

        return tuple(screenshot), tuple(click)

    def run(self):
        if self.config.Benchmark_TestScene == 'input':
            return self.run_simple_input_benchmark()

        self.config.override(Emulator_ScreenshotMethod='ADB')
        self.device.uninstall_minicap()
        self.ensure_campaign_ui('7-2', mode='normal')

        logger.attr('DeviceType', self.config.Benchmark_DeviceType)
        logger.attr('TestScene', self.config.Benchmark_TestScene)
        screenshot, click = self.get_test_methods()
        self.benchmark(screenshot, click)
        if 'input' in self.config.Benchmark_TestScene:
            self.run_simple_input_benchmark()

    def run_simple_input_benchmark(self):
        return InputBenchmark(self.device).run()

    def run_simple_screenshot_benchmark(self):
        """
        Returns:
            str: The fastest screenshot method on current device.
        """
        screenshot = ['ADB', 'ADB_nc', 'uiautomator2', 'aScreenCap', 'aScreenCap_nc', 'DroidCast', 'DroidCast_raw']

        def remove(*args):
            return [l for l in screenshot if l not in args]

        sdk = self.device.sdk_ver
        logger.info(f'sdk_ver: {sdk}')
        if not (21 <= sdk <= 28):
            screenshot = remove('aScreenCap', 'aScreenCap_nc')
        if self.device.is_chinac_phone_cloud:
            screenshot = remove('ADB_nc', 'aScreenCap_nc')
        if self.device.nemu_ipc_available():
            screenshot.append('nemu_ipc')
        if self.device.ldopengl_available():
            screenshot.append('ldopengl')
        screenshot = tuple(screenshot)

        self.TEST_TOTAL = 3
        self.TEST_BEST = 1
        method, _ = self.benchmark(screenshot, tuple())

        return method


def run_benchmark(config):
    try:
        Benchmark(config, task='Benchmark').run()
        return True
    except RequestHumanTakeover:
        logger.critical('Request human takeover')
        return False


class InputBenchmark:
    """Compare verified text replacements in a disposable Android Settings field."""

    TEST_TOTAL = 3
    TEST_TEXT = 'Aa09+/' * 32 + '='
    TEXTBOX_XPATH = (
        '(//*[@enabled="true" and not(@password="true") and not(@visible-to-user="false") and '
        '(@class="android.widget.EditText" or @class="android.widget.AutoCompleteTextView" '
        'or @class="android.widget.MultiAutoCompleteTextView")])[1]'
    )
    IME_SETTINGS = ('default_input_method', 'enabled_input_methods', 'show_ime_with_hard_keyboard')

    def __init__(self, device):
        self.device = device
        self.results = {}
        self.preparation = {}
        self.failures = {}

    def _setting(self, name):
        return self.device.adb_shell(['settings', 'get', 'secure', name]).strip()

    def _prepare_uiautomator(self):
        packages = ('com.github.uiautomator', 'com.github.uiautomator.test')
        if any(not self.device.adb_shell(['pm', 'path', package]).startswith('package:') for package in packages):
            self.device.install_uiautomator2()
        _ = self.device.u2.info

    def _restore_ime(self, settings):
        def restore(name):
            value = settings[name]
            if self._setting(name) == value:
                return
            command = ['settings', 'delete', 'secure', name] if value == 'null' else [
                'settings', 'put', 'secure', name, value]
            self.device.adb_shell(' '.join(shlex.quote(arg) for arg in command))

        # Re-enable the original IMEs before restoring the selected service.
        restore('enabled_input_methods')
        selected = settings['default_input_method']
        if selected and selected != 'null' and self.device.current_ime()[0] != selected:
            self.device.u2.shell(['ime', 'enable', selected])
            self.device.u2.shell(['ime', 'set', selected])
        for name in self.IME_SETTINGS:
            restore(name)
        if any(self._setting(name) != value for name, value in settings.items()):
            raise RuntimeError('Cannot restore Android keyboard settings after the input benchmark')
        if selected and selected != 'null' and self.device.current_ime()[0] != selected:
            raise RuntimeError('Cannot restore the original IME after the input benchmark')

    def _restore_task(self, task):
        self.device.adb_shell(['am', 'task', 'focus', str(task)], timeout=15)
        deadline = time.monotonic() + 5
        while self.device._foreground_task_uiautomator2() != task:
            if time.monotonic() >= deadline:
                raise RuntimeError('Cannot restore the foreground app after the input benchmark')
            self.device.sleep(0.2)

    def _button(self, xpath):
        hierarchy = self.device.dump_hierarchy_uiautomator2()
        return HierarchyButton(hierarchy, xpath)

    def _textbox(self):
        button = self._button(self.TEXTBOX_XPATH)
        if not button:
            raise RuntimeError('Settings search textbox is no longer available')
        return button

    def _open_textbox(self):
        actions = ['android.settings.SETTINGS', 'android.settings.MANAGE_ALL_APPLICATIONS_SETTINGS']
        # Android 15 Settings has a search bar; older Settings exposes app-list search.
        if self.device.sdk_ver < 35:
            actions.reverse()
        search_ids = (
            'com.android.settings:id/search_action_bar', 'com.android.settings:id/search_bar',
            'com.android.settings:id/search_app_list_menu', 'android:id/search_button',
        )
        for action in actions:
            self.device.adb_shell(['am', 'start', '-W', '-a', action], timeout=15)
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                hierarchy = self.device.dump_hierarchy_uiautomator2()
                button = HierarchyButton(hierarchy, self.TEXTBOX_XPATH)
                if button:
                    return
                for resource_id in search_ids:
                    button = HierarchyButton(hierarchy, f'//*[@resource-id="{resource_id}" and @clickable="true"]')
                    if button:
                        self.device.click(button, control_check=False)
                        break
                self.device.sleep(0.3)
        raise RuntimeError('Cannot open a native Settings search textbox for the input benchmark')

    def _trial(self, input_text):
        self.device.click(self._textbox(), control_check=False)
        # Setup and observation use native accessibility, independently of either backend.
        if self.device.u2(focused=True).set_text('StaleInput42') is False:
            raise RuntimeError('Cannot prefill the benchmark textbox')
        button = self._textbox()
        if button.attrib.get('text') != 'StaleInput42':
            raise RuntimeError('Cannot verify the benchmark prefill')
        start = time.perf_counter()
        success = input_text(self.TEST_TEXT, focus=lambda: self.device.click(button, control_check=False), clear=True)
        elapsed = time.perf_counter() - start
        if not success or self._textbox().attrib.get('text') != self.TEST_TEXT:
            raise RuntimeError('Input method did not replace the textbox with the exact benchmark text')
        return elapsed

    def _clear_textbox(self):
        self.device.click(self._textbox(), control_check=False)
        cleared = self.device.u2(focused=True).clear_text()
        # Empty Android editors may expose their hint (e.g. "Search settings") as text.
        if cleared is False or self._textbox().attrib.get('text') in (self.TEST_TEXT, 'StaleInput42'):
            raise RuntimeError('Cannot clear the Settings benchmark textbox')
        self.device.adb_shell(['input', 'keyevent', 'KEYCODE_BACK'])

    def run(self):
        logger.hr('Input benchmark', level=1)
        logger.info(f'Testing {len(self.TEST_TEXT)} ASCII characters, median of {self.TEST_TOTAL} replacements')
        settings = {name: self._setting(name) for name in self.IME_SETTINGS}
        task = self.device._foreground_task_uiautomator2()
        if task is None:
            raise RequestHumanTakeover('Cannot identify the foreground app before the input benchmark')
        try:
            # Both backends need native accessibility; FastInputIME comes in the same APK.
            self._prepare_uiautomator()
            for method in ('ADB', 'FastInputIME'):
                backend = self.device.input_methods[method]
                opened = False
                try:
                    if not backend['supported']():
                        raise RuntimeError('Unsupported with the selected control method')
                    start = time.perf_counter()
                    if not backend['prepare']():
                        raise RuntimeError('Input method preparation failed')
                    self.preparation[method] = time.perf_counter() - start
                    logger.attr(f'{method} preparation', f'{self.preparation[method]:.3f}s')
                    # IME preparation can navigate away; open the field afterward.
                    self._open_textbox()
                    opened = True
                    self._trial(backend['input'])  # Untimed warmup; still require correct replacement.
                    samples = []
                    for index in range(self.TEST_TOTAL):
                        elapsed = self._trial(backend['input'])
                        samples.append(elapsed)
                        logger.attr(f'{method} {index + 1}/{self.TEST_TOTAL}', f'{elapsed:.3f}s')
                    self.results[method] = statistics.median(samples)
                except Exception as error:
                    self.failures[method] = str(error)
                    logger.warning(f'Input benchmark failed for {method}: {error}')
                finally:
                    if opened:
                        self._clear_textbox()
        finally:
            try:
                self._restore_ime(settings)
            finally:
                self._restore_task(task)
                self.device.stuck_record_clear()
        for method, elapsed in self.results.items():
            logger.attr(f'{method} input', f'{elapsed:.3f}s')
        if not self.results:
            raise RequestHumanTakeover('No input method passed the benchmark; select an input method in Alas settings')
        fastest = min(self.results, key=self.results.get)
        logger.info(f'Recommend input method: {fastest} ({self.results[fastest]:.3f}s)')
        return fastest
