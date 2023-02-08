import time
import typing as t

import numpy as np
from rich.table import Table
from rich.text import Text

from module.base.utils import float2str as float2str_
from module.base.utils import random_rectangle_point
from module.campaign.campaign_ui import CampaignUI
from module.daemon.daemon_base import DaemonBase
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
            start = time.time()

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

            cost = time.time() - start
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

        if cost < 0.10:
            return Text('Ultra Fast', style="bold bright_green")
        if cost < 0.20:
            return Text('Very Fast', style="bright_green")
        if cost < 0.30:
            return Text('Fast', style="green")
        if cost < 0.50:
            return Text('Medium', style="yellow")
        if cost < 0.75:
            return Text('Slow', style="red")
        if cost < 1.00:
            return Text('Very Slow', style="bright_red")
        return Text('Ultra Slow', style="bold bright_red")

    @staticmethod
    def evaluate_click(cost):
        if not isinstance(cost, (float, int)):
            return Text(cost, style="bold bright_red")

        if cost < 0.1:
            return Text('Fast', style="bright_green")
        if cost < 0.2:
            return Text('Medium', style="yellow")
        if cost < 0.4:
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
            logger.info(f'Recommend control method: {fastest[0]} ({float2str(fastest[1])})')
            fastest_click = fastest[0]

        return fastest_screenshot, fastest_click

    def get_test_methods(self) -> t.Tuple[t.Tuple[str], t.Tuple[str]]:
        device = self.config.Benchmark_DeviceType
        # device == 'emulator'
        screenshot = ['ADB', 'ADB_nc', 'uiautomator2', 'aScreenCap', 'aScreenCap_nc', 'DroidCast', 'DroidCast_raw']
        click = ['ADB', 'uiautomator2', 'minitouch']

        def remove(*args):
            return [l for l in screenshot if l not in args]

        # No ascreencap on Android > 9
        if device in ['emulator_android_12', 'android_phone_12']:
            screenshot = remove('aScreenCap', 'aScreenCap_nc')
        # No nc loopback
        if device in ['plone_cloud_with_adb']:
            screenshot = remove('ADB_nc', 'aScreenCap_nc')
        # VMOS
        if device == 'android_phone_vmos':
            screenshot = ['ADB', 'aScreenCap', 'DroidCast', 'DroidCast_raw']
            click = ['ADB', 'Hermit', 'MaaTouch']

        scene = self.config.Benchmark_TestScene
        if 'screenshot' not in scene:
            screenshot = []
        if 'click' not in scene:
            click = []

        return tuple(screenshot), tuple(click)

    def run(self):
        self.config.override(Emulator_ScreenshotMethod='ADB')
        self.device.uninstall_minicap()
        self.ui_goto_campaign()
        self.campaign_set_chapter('7-2')

        logger.attr('DeviceType', self.config.Benchmark_DeviceType)
        logger.attr('TestScene', self.config.Benchmark_TestScene)
        screenshot, click = self.get_test_methods()
        self.benchmark(screenshot, click)

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
        screenshot = tuple(screenshot)

        self.TEST_TOTAL = 3
        self.TEST_BEST = 1
        method, _ = self.benchmark(screenshot, tuple())

        return method


if __name__ == '__main__':
    b = Benchmark('alas', task='Benchmark')
    b.run()
