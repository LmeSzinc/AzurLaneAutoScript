import json
from functools import wraps

import requests
from adbutils.errors import AdbError

from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import point2str, random_rectangle_point
from module.device.method.adb import Adb
from module.device.method.utils import (RETRY_TRIES, handle_unknown_host_service, retry_sleep,
                                        HierarchyButton, handle_adb_error)
from module.exception import RequestHumanTakeover
from module.logger import logger


class HermitError(Exception):
    pass


def retry(func):
    @wraps(func)
    def retry_wrapper(self, *args, **kwargs):
        """
        Args:
            self (Hermit):
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
            # When unable to send requests
            except requests.exceptions.ConnectionError as e:
                logger.error(e)
                text = str(e)
                if 'Connection aborted' in text:
                    # Hermit not installed or not running
                    # ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
                    def init():
                        self.adb_reconnect()
                        self.hermit_init()
                else:
                    # Lost connection, adb server was killed
                    # HTTPConnectionPool(host='127.0.0.1', port=20269):
                    # Max retries exceeded with url: /click?x=500&y=500
                    def init():
                        self.adb_reconnect()
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
            # HermitError: {"code":-1,"msg":"error"}
            except HermitError as e:
                logger.error(e)

                def init():
                    self.adb_reconnect()
                    self.hermit_init()
            # Unknown, probably a trucked image
            except Exception as e:
                logger.exception(e)

                def init():
                    pass

        logger.critical(f'Retry {func.__name__}() failed')
        raise RequestHumanTakeover

    return retry_wrapper


class Hermit(Adb):
    """
    Hermit, https://github.com/LookCos/hermit.
    API docs: https://www.lookcos.cn/docs/hermit#/zh-cn/API

    True, Hermit has other control APIs and screenshot APIs but they ALL WORK LIKE SHIT.
    Hermit screenshot is slower than ADB and you are likely to get request timeout or trucked images.
    Thus, it requests root permission every time,
    so you will get a toast showing forever: Superuser granted to Hermit.

    Hermit is added to Alas in order to have a better performance in vmos which can't run uiautomator2 and minitouch.
    Note that Hermit requires Android>=7.0
    """
    _hermit_port = 9999
    _hermit_package_name = 'com.lookcos.hermit'

    @property
    def _hermit_url(self):
        return f'http://127.0.0.1:{self._hermit_port}'

    def hermit_init(self):
        logger.hr('Hermit init')

        self.app_stop_adb(self._hermit_package_name)
        # self.uninstall_hermit()

        logger.info('Try to start hermit')
        if self.app_start_adb(self._hermit_package_name, allow_failure=True):
            # Success to start hermit
            logger.info('Success to start hermit')
        else:
            # Hermit not installed
            logger.warning(f'{self._hermit_package_name} not found, installing hermit')
            self.adb_command(['install', '-t', self.config.HERMIT_FILEPATH_LOCAL])
            self.app_start_adb(self._hermit_package_name)

        # Enable accessibility service
        self.hermit_enable_accessibility()

        # Hide Hermit
        # 0 -->  "KEYCODE_UNKNOWN"
        # 1 -->  "KEYCODE_MENU"
        # 2 -->  "KEYCODE_SOFT_RIGHT"
        # 3 -->  "KEYCODE_HOME"
        # 4 -->  "KEYCODE_BACK"
        # 5 -->  "KEYCODE_CALL"
        # 6 -->  "KEYCODE_ENDCALL"
        self.adb_shell(['input', 'keyevent', '3'])

        # Switch back to AzurLane
        self.app_start_adb()

    def uninstall_hermit(self):
        self.adb_command(['uninstall', self._hermit_package_name])

    def hermit_enable_accessibility(self):
        """
        Turn on accessibility service for Hermit.

        Raises:
            RequestHumanTakeover: If failed and user should do it manually.
        """
        logger.hr('Enable accessibility service')
        interval = Timer(0.3)
        timeout = Timer(10, count=10).start()
        while 1:
            h = self.dump_hierarchy_adb()
            interval.wait()
            interval.reset()

            def appear(xpath):
                return bool(HierarchyButton(h, xpath))

            def appear_then_click(xpath):
                b = HierarchyButton(h, xpath)
                if b:
                    point = random_rectangle_point(b.button)
                    logger.info(f'Click {point2str(*point)} @ {b}')
                    self.click_adb(*point)
                    return True
                else:
                    return False

            if appear_then_click('//*[@text="Hermit" and @resource-id="android:id/title"]'):
                continue
            if appear_then_click('//*[@class="android.widget.Switch" and @checked="false"]'):
                continue
            if appear_then_click('//*[@resource-id="android:id/button1"]'):
                # Just plain click here
                # Can't use uiautomator once hermit has access to accessibility service,
                # or uiautomator will get the access.
                break
            if appear('//*[@class="android.widget.Switch" and @checked="true"]'):
                raise HermitError('Accessibility service already enable but get error')

            # End
            if timeout.reached():
                logger.critical('Unable to turn on accessibility service for Hermit')
                logger.critical(
                    '\n\n'
                    'Please do this manually:\n'
                    '1. Find "Hermit" in accessibility setting and click it\n'
                    '2. Turn it ON and click OK\n'
                    '3. Switch back to AzurLane\n'
                )
                raise RequestHumanTakeover

    @cached_property
    def hermit_session(self):
        session = requests.Session()
        session.trust_env = False  # Ignore proxy
        self._hermit_port = self.adb_forward('tcp:9999')
        return session

    def hermit_send(self, url, **kwargs):
        """
        Args:
            url (str):
            **kwargs:

        Returns:
            dict: Usually to be {"code":0,"msg":"ok"}
        """
        result = self.hermit_session.get(f'{self._hermit_url}{url}', params=kwargs, timeout=3).text
        try:
            result = json.loads(result, encoding='utf-8')
            if result['code'] != 0:
                # {"code":-1,"msg":"error"}
                raise HermitError(result)
        except (json.decoder.JSONDecodeError, KeyError):
            e = HermitError(result)
            if 'GestureDescription$Builder' in result:
                logger.error(e)
                logger.critical('Hermit cannot run on current device, hermit requires Android>=7.0')
                raise RequestHumanTakeover
            if 'accessibilityservice' in result:
                # Attempt to invoke virtual method
                # 'boolean android.accessibilityservice.AccessibilityService.dispatchGesture(
                #     android.accessibilityservice.GestureDescription,
                #     android.accessibilityservice.AccessibilityService$GestureResultCallback,
                #     android.os.Handler
                # )' on a null object reference
                logger.error('Unable to access accessibility service')
            raise e

        # Hermit only takes 2-4ms
        # Add a 50ms delay because game can't response quickly.
        self.sleep(0.05)
        return result

    @retry
    def click_hermit(self, x, y):
        self.hermit_send('/click', x=x, y=y)
