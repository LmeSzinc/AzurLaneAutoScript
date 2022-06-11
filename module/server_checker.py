import random
from collections import deque
from json import JSONDecodeError

import requests

from module.base.timer import Timer
from module.exception import ScriptError
from module.logger import logger


class ServerChecker:
    def __init__(self, server: str) -> None:
        self._base: dict = {
            'cn_android': '',
            'cn_ios': '',
            'cn_channel': '',
            'en': '',
            'en_channel': '',
            'disabled': ''
        }

        self._UA: list = [
            'Dalvik/2.1.0 (Linux; U; Android 6.0.1; MuMu Build/V417IR)',
        ]

        if server not in self._base:
            logger.warning(f'Unsupported server platform "{server}" for server checker.')
            logger.warning('Disable server checker by default.')
            server = 'disabled'

        self._server: str = server
        self._state: deque = deque(maxlen=2)
        self._reason: str = ''
        self._interval: int = 0
        self._timer: Timer = Timer(60 * 5)   # check per 5 mins

        self.check_now()

    def _load_server(self) -> None:
        """
        Get server status using API.
        Set reason if server is unavailable.

        ScriptError will be raised if somthing is wrong with API.
        """
        if self._server == 'disabled':
            self._state.append(True)
            return

        try:
            resp = requests.get(
                # the last '?' will be escaped if use params, don't do so
                url=f'{self._base[self._server]}?cmd=load_server?',
                headers={
                    'User-Agent': f'{random.choice(self._UA)}',
                    'Accept-Encoding': 'gzip',
                    'Accept': '*/*',
                    'Connection': 'Keep-Alive',
                    'X-Unity-Version': '2018.4.34f1',
                    'Host': f'{self._base[self._server]}'
                },
                timeout=3,
            )
            if resp.ok:
                j = resp.json()
                server_state = sum([1 if server['state'] == 1 else 0 for server in j])
                if server_state / len(j) > 0.5:
                    self._reason = f'The server "{self._server}" is being maintained. Please wait'
                    self._state.append(False)
                else:
                    self._state.append(True)
            else:
                self._reason = f'Server "{self._server}" return status code {resp.status_code}'
                self._state.append(False)
                raise ScriptError(self._reason)
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout):
            self._reason = 'Unable to connect to the server. Please check your network status'
            self._state.append(False)
        except JSONDecodeError:
            self._reason = f'Response of "{self._server}" seems not to be a JSON'
            self._state.append(False)
            raise ScriptError(self._reason)
        except Exception as e:
            self._reason = str(e)
            self._state.append(False)

    def wait_until_available(self) -> None:
        while not self.is_available():
            self._timer.wait()
            self.check_now()

    def check_now(self) -> None:
        """
        Ignore timer and get server status immediately.

        If server is available, timer will be set to 30 mins.
        Otherwise, timer will gradually increases from 1 to 5 min(s).

        If a ScriptError occurs, server checker will be temporarily forced off.
        """
        try:
            self._load_server()
            if self._state[-1]:
                self._interval = 0
            else:
                if self._interval < 5:
                    self._interval += 1

            # Only show reason when server is unavailable.
            if not self._state[-1]:
                if "Unable" in self._reason:
                    logger.warning(f'{self._reason}. Server checker will retry after {self._interval} mins')
                else:
                    logger.info(f'{self._reason}. Server checker will retry after {self._interval} mins')
        except ScriptError as e:
            logger.critical(e)
            logger.warning('There may be something wrong with server checker.')
            logger.warning('Server checker will be temporarily forced off.')
            self._server = 'disabled'
            self._interval = 0
            self._state.clear()
            self._state.append(True)
        finally:
            self._timer.limit = 60 * (30 if self._interval == 0 else self._interval)
            self._timer.reset()

    def is_available(self) -> bool:
        """
        Return server status using cache.

        Returns:
            bool: True if server is available.
        """
        if self._interval != 0 and self._timer.reached():
            self.check_now()

        return self._state[-1]  # return the latest state

    def is_recovered(self) -> bool:
        """
        Returns:
            bool: True if server is recovered from an unavailable state.
        """
        if len(self._state) < 2:
            return False

        return self._state[0] is False and self._state[-1] is True

    def is_after_maintenance(self) -> bool:
        """
        Reason will only be updated when server is unavailable
        Thus, client need to reesart when server recovers
        with keyword 'maintained' in self._reason

        Returns:
            bool: True if server is after maintenance.
        """
        if self._server == 'disabled':
            return False
        if not self._state[-1]:
            return False

        return 'maintained' in self._reason

    def is_enabled(self) -> bool:
        return self._server != 'disabled'
