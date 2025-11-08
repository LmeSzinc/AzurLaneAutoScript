from lxml import etree

from module.base.timer import Timer
from module.device.method.adb import Adb
from module.device.method.uiautomator_2 import Uiautomator2
from module.device.method.utils import HierarchyButton
from module.device.method.wsa import WSA
from module.exception import ScriptError
from module.logger import logger


class AppControl(Adb, WSA, Uiautomator2):
    hierarchy: etree._Element
    _app_u2_family = ['uiautomator2', 'minitouch', 'scrcpy', 'MaaTouch', 'nemu_ipc']
    _hierarchy_interval = Timer(0.1)

    def app_current(self) -> str:
        method = self.config.Emulator_ControlMethod
        if self.is_wsa:
            package = self.app_current_wsa()
        elif method in AppControl._app_u2_family:
            package = self.app_current_uiautomator2()
        else:
            package = self.app_current_adb()
        package = package.strip(' \t\r\n')
        return package

    def app_is_running(self) -> bool:
        package = self.app_current()
        logger.attr('Package_name', package)
        return package == self.package

    def app_start(self):
        method = self.config.Emulator_ControlMethod
        logger.info(f'App start: {self.package}')
        if self.config.Emulator_Serial == 'wsa-0':
            self.app_start_wsa(display=0)
        elif method in AppControl._app_u2_family:
            self.app_start_uiautomator2()
        else:
            self.app_start_adb()

    def app_stop(self):
        method = self.config.Emulator_ControlMethod
        logger.info(f'App stop: {self.package}')
        if method in AppControl._app_u2_family:
            self.app_stop_uiautomator2()
        else:
            self.app_stop_adb()

    def hierarchy_timer_set(self, interval=None):
        if interval is None:
            interval = 0.1
        elif isinstance(interval, (int, float)):
            # No limitation for manual set in code
            pass
        else:
            logger.warning(f'Unknown hierarchy interval: {interval}')
            raise ScriptError(f'Unknown hierarchy interval: {interval}')

        if interval != self._hierarchy_interval.limit:
            logger.info(f'Hierarchy interval set to {interval}s')
            self._hierarchy_interval.limit = interval

    def dump_hierarchy(self) -> etree._Element:
        """
        Returns:
            etree._Element: Select elements with `self.hierarchy.xpath('//*[@text="Hermit"]')` for example.
        """
        self._hierarchy_interval.wait()
        self._hierarchy_interval.reset()

        method = self.config.Emulator_ControlMethod
        if method in AppControl._app_u2_family:
            self.hierarchy = self.dump_hierarchy_uiautomator2()
        else:
            self.hierarchy = self.dump_hierarchy_adb()
        return self.hierarchy

    def xpath_to_button(self, xpath: str) -> HierarchyButton:
        """
        Args:
            xpath (str):

        Returns:
            HierarchyButton:
                An object with methods and properties similar to Button.
                If element not found or multiple elements were found, return None.
        """
        return HierarchyButton(self.hierarchy, xpath)
