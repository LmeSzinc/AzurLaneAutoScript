import typing as t
from dataclasses import dataclass
from functools import wraps
from json.decoder import JSONDecodeError
from subprocess import list2cmdline

import uiautomator2 as u2
from adbutils.errors import AdbError
from lxml import etree

from module.base.utils import *
from module.device.connection import Connection
from module.device.method.utils import (ImageTruncated, PackageNotInstalled, RETRY_TRIES, handle_adb_error,
                                        handle_unknown_host_service, possible_reasons, retry_sleep)
from module.exception import RequestHumanTakeover
from module.logger import logger


def retry(func):
    @wraps(func)
    def retry_wrapper(self, *args, **kwargs):
        """
        Args:
            self (Uiautomator2):
        """
        init = None
        for _ in range(RETRY_TRIES):
            try:
                if callable(init):
                    retry_sleep(_)
                    init()
                return func(self, *args, **kwargs)
            # Can't handle
            except RequestHumanTakeover:
                break
            # When adb server was killed
            except ConnectionResetError as e:
                logger.error(e)

                def init():
                    self.adb_reconnect()
            # In `device.set_new_command_timeout(604800)`
            # json.decoder.JSONDecodeError: Expecting value: line 1 column 2 (char 1)
            except JSONDecodeError as e:
                logger.error(e)

                def init():
                    self.install_uiautomator2()
            # AdbError
            except AdbError as e:
                if handle_adb_error(e):
                    def init():
                        self.adb_reconnect()
                elif handle_unknown_host_service(e):
                    def init():
                        self.adb_start_server()
                        self.adb_reconnect()
                else:
                    break
            # RuntimeError: USB device 127.0.0.1:5555 is offline
            except RuntimeError as e:
                if handle_adb_error(e):
                    def init():
                        self.adb_reconnect()
                else:
                    break
            # In `assert c.read string(4) == _OKAY`
            # ADB on emulator not enabled
            except AssertionError as e:
                logger.exception(e)
                possible_reasons(
                    'If you are using BlueStacks or LD player or WSA, '
                    'please enable ADB in the settings of your emulator'
                )
                break
            # Package not installed
            except PackageNotInstalled as e:
                logger.error(e)

                def init():
                    self.detect_package()
            # ImageTruncated
            except ImageTruncated as e:
                logger.error(e)

                def init():
                    pass
            # Unknown
            except Exception as e:
                logger.exception(e)

                def init():
                    pass

        logger.critical(f'Retry {func.__name__}() failed')
        raise RequestHumanTakeover

    return retry_wrapper


@dataclass
class ProcessInfo:
    pid: int
    ppid: int
    thread_count: int
    cmdline: str
    name: str


@dataclass
class ShellBackgroundResponse:
    success: bool
    pid: int
    description: str


class Uiautomator2(Connection):
    @retry
    def screenshot_uiautomator2(self):
        image = self.u2.screenshot(format='raw')
        image = np.frombuffer(image, np.uint8)
        if image is None:
            raise ImageTruncated('Empty image after reading from buffer')

        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        if image is None:
            raise ImageTruncated('Empty image after cv2.imdecode')

        cv2.cvtColor(image, cv2.COLOR_BGR2RGB, dst=image)
        if image is None:
            raise ImageTruncated('Empty image after cv2.cvtColor')

        return image

    @retry
    def click_uiautomator2(self, x, y):
        self.u2.click(x, y)

    @retry
    def long_click_uiautomator2(self, x, y, duration=(1, 1.2)):
        self.u2.long_click(x, y, duration=duration)

    @retry
    def swipe_uiautomator2(self, p1, p2, duration=0.1):
        self.u2.swipe(*p1, *p2, duration=duration)

    @retry
    def _drag_along(self, path):
        """Swipe following path.

        Args:
            path (list): (x, y, sleep)

        Examples:
            al.drag_along([
                (403, 421, 0.2),
                (821, 326, 0.1),
                (821, 326-10, 0.1),
                (821, 326+10, 0.1),
                (821, 326, 0),
            ])
            Equals to:
            al.device.touch.down(403, 421)
            time.sleep(0.2)
            al.device.touch.move(821, 326)
            time.sleep(0.1)
            al.device.touch.move(821, 326-10)
            time.sleep(0.1)
            al.device.touch.move(821, 326+10)
            time.sleep(0.1)
            al.device.touch.up(821, 326)
        """
        length = len(path)
        for index, data in enumerate(path):
            x, y, second = data
            if index == 0:
                self.u2.touch.down(x, y)
                logger.info(point2str(x, y) + ' down')
            elif index - length == -1:
                self.u2.touch.up(x, y)
                logger.info(point2str(x, y) + ' up')
            else:
                self.u2.touch.move(x, y)
                logger.info(point2str(x, y) + ' move')
            self.sleep(second)

    def drag_uiautomator2(self, p1, p2, segments=1, shake=(0, 15), point_random=(-10, -10, 10, 10),
                          shake_random=(-5, -5, 5, 5), swipe_duration=0.25, shake_duration=0.1):
        """Drag and shake, like:
                     /\
        +-----------+  +  +
                        \/
        A simple swipe or drag don't work well, because it only has two points.
        Add some way point to make it more like swipe.

        Args:
            p1 (tuple): Start point, (x, y).
            p2 (tuple): End point, (x, y).
            segments (int):
            shake (tuple): Shake after arrive end point.
            point_random: Add random to start point and end point.
            shake_random: Add random to shake array.
            swipe_duration: Duration between way points.
            shake_duration: Duration between shake points.
        """
        p1 = np.array(p1) - random_rectangle_point(point_random)
        p2 = np.array(p2) - random_rectangle_point(point_random)
        path = [(x, y, swipe_duration) for x, y in random_line_segments(p1, p2, n=segments, random_range=point_random)]
        path += [
            (*p2 + shake + random_rectangle_point(shake_random), shake_duration),
            (*p2 - shake - random_rectangle_point(shake_random), shake_duration),
            (*p2, shake_duration)
        ]
        path = [(int(x), int(y), d) for x, y, d in path]
        self._drag_along(path)

    @retry
    def app_current_uiautomator2(self):
        """
        Returns:
            str: Package name.
        """
        result = self.u2.app_current()
        return result['package']

    @retry
    def app_start_uiautomator2(self, package_name=None):
        if not package_name:
            package_name = self.package
        try:
            self.u2.app_start(package_name)
        except u2.exceptions.BaseError as e:
            # BaseError: package "com.bilibili.azurlane" not found
            logger.error(e)
            raise PackageNotInstalled(package_name)

    @retry
    def app_stop_uiautomator2(self, package_name=None):
        if not package_name:
            package_name = self.package
        self.u2.app_stop(package_name)

    @retry
    def dump_hierarchy_uiautomator2(self) -> etree._Element:
        content = self.u2.dump_hierarchy(compressed=True)
        hierarchy = etree.fromstring(content.encode('utf-8'))
        return hierarchy

    def uninstall_uiautomator2(self):
        logger.info('Removing uiautomator2')
        for file in [
            'app-uiautomator.apk',
            'app-uiautomator-test.apk',
            'minitouch',
            'minitouch.so',
            'atx-agent',
        ]:
            self.adb_shell(["rm", f"/data/local/tmp/{file}"])

    @retry
    def resolution_uiautomator2(self, cal_rotation=True) -> t.Tuple[int, int]:
        """
        Faster u2.window_size(), cause that calls `dumpsys display` twice.

        Returns:
            (width, height)
        """
        info = self.u2.http.get('/info').json()
        w, h = info['display']['width'], info['display']['height']
        if cal_rotation:
            rotation = self.get_orientation()
            if (w > h) != (rotation % 2 == 1):
                w, h = h, w
        return w, h

    def resolution_check_uiautomator2(self):
        """
        Alas does not actively check resolution but the width and height of screenshots.
        However, some screenshot methods do not provide device resolution, so check it here.

        Returns:
            (width, height)

        Raises:
            RequestHumanTakeover: If resolution is not 1280x720
        """
        width, height = self.resolution_uiautomator2()
        logger.attr('Screen_size', f'{width}x{height}')
        if width == 1280 and height == 720:
            return (width, height)
        if width == 720 and height == 1280:
            return (width, height)

        logger.critical(f'Resolution not supported: {width}x{height}')
        logger.critical('Please set emulator resolution to 1280x720')
        raise RequestHumanTakeover

    @retry
    def proc_list_uiautomator2(self) -> t.List[ProcessInfo]:
        """
        Get info about current processes.
        """
        resp = self.u2.http.get("/proc/list", timeout=10)
        resp.raise_for_status()
        result = [
            ProcessInfo(
                pid=proc['pid'],
                ppid=proc['ppid'],
                thread_count=proc['threadCount'],
                cmdline=' '.join(proc['cmdline']) if proc['cmdline'] is not None else '',
                name=proc['name'],
            ) for proc in resp.json()
        ]
        return result

    @retry
    def u2_shell_background(self, cmdline, timeout=10) -> ShellBackgroundResponse:
        """
        Run at background.

        Note that this function will always return a success response,
        as this is a untested and hidden method in ATX.
        """
        if isinstance(cmdline, (list, tuple)):
            cmdline = list2cmdline(cmdline)
        elif isinstance(cmdline, str):
            cmdline = cmdline
        else:
            raise TypeError("cmdargs type invalid", type(cmdline))

        data = dict(command=cmdline, timeout=str(timeout))
        ret = self.u2.http.post("/shell/background", data=data, timeout=timeout + 10)
        ret.raise_for_status()

        resp = ret.json()
        resp = ShellBackgroundResponse(
            success=bool(resp.get('success', False)),
            pid=resp.get('pid', 0),
            description=resp.get('description', '')
        )
        return resp
