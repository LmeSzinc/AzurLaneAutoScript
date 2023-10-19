from collections import deque
from json import JSONDecodeError

import requests

from module.base.timer import Timer
from module.config.server import VALID_SERVER_LIST as server_list
from module.exception import ScriptError
from module.logger import logger


class ServerChecker:
    def __init__(self, server: str) -> None:
        self._base: str = 'http://sc.shiratama.cn'
        self._api: dict = {
            'get_state': '/server/get_state',           # post
            'get_all_state': '/server/get_all_state',   # post
            'list': '/server/list'                      # get
        }

        if server != 'disabled':
            server = server.split('-')
            server = server_list[server[0]][int(server[-1])]

        self._server: str = server
        self._state: deque = deque(maxlen=2)
        self._timestamp: int = 0
        self._expired: int = 0
        self._timer: Timer = Timer(0)

        # Status flags
        self._recover: bool = False
        self._retry: bool = False

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
            session = requests.Session()
            session.trust_env = False
            resp = session.post(
                url=f'{self._base}{self._api["get_state"]}',
                params={
                    'server_name': self._server
                },
                timeout=15
            )
            if resp.status_code == 200:
                j = resp.json()
                if j['state'] != 1:
                    self._state.append(True)
                    logger.info(f'Server "{self._server}" is available.')
                else:
                    self._state.append(False)
                    logger.info(f'Server "{self._server}" is under maintenance.')

                # Check if API server was died
                if j['last_update'] > self._timestamp:
                    self._timestamp = j['last_update']
                    self._expired = 0
                else:
                    self._expired += 1
                    if self._expired > 3:
                        logger.warning(f'Timestamp {self._timestamp} has not been updated for 3 times.')
            elif resp.status_code == 404:
                self._state.append(False)
                raise ScriptError(f'Server "{self._server}" does not exist!')
            else:
                raise ScriptError(f'Get status_code {resp.status_code}. Response is {resp.text}')
        except (requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout) as e:
            logger.error(e)
            logger.error('Timeout while connecting to server checker API.')
            if self._retry:
                self._state.append(False)
            else:
                self._state.append(self.fast_retry())
        except JSONDecodeError:
            self._state.append(False)
            raise ScriptError(f'Response "{resp.text}" seems not to be a JSON.')
        except Exception as e:
            logger.error(e)
            self._state.append(False)
            raise e

    def wait_until_available(self) -> None:
        while not self.is_available():
            self._timer.wait()
            self.check_now()

    def check_now(self) -> None:
        """
        Ignore timer and get server status immediately.

        If server is available, server checker will keep silence.
        Otherwise, timer will gradually increases from 2 to 10 min(s).

        If a ScriptError occurs, server checker will be temporarily forced off.
        """
        try:
            self._load_server()
            if self._state[-1]:
                self._timer.limit = 0
                # Recover means state[-1] is True and state[0] is False
                if not self._state[0]:
                    self._recover = True
            else:
                if self._timer.limit < 600:
                    self._timer.limit += 120
                logger.info(f'Server checker will retry after {self._timer.limit}s')
            self._timer.reset()
        except ScriptError as e:
            logger.warning(str(e))
            logger.warning('There may be something wrong with server checker.')
            logger.warning('Please contact the developer to fix it.')
            logger.warning('Server checker will be temporarily forced off.')
            self.reset()
            self._server = 'disabled'
            self._recover = True
            self._state.append(True)
        except Exception as e:
            raise e

    def reset(self) -> None:
        self._timestamp = 0
        self._expired = 0
        self._timer.limit = 0
        self._recover = False

    def is_available(self) -> bool:
        """
        Return server status using cache.

        Returns:
            bool: True if server is available.
        """
        if self._timer.limit != 0 and self._timer.reached():
            self.check_now()

        return self._state[-1]  # return the latest state

    def is_recovered(self) -> bool:
        """
        Returns:
            bool: True if server is recovered from an unavailable state.
        """
        if len(self._state) < 2:
            self._recover = False
            return False

        if self._recover:
            self._recover = False
            return True

        return False

    def fast_retry(self) -> bool:
        """
        Sometimes CN users may fail to connect to the API even when the network is available.
        Thus, it need another trusty site to judge the network status.
        Here choose Baidu.

        Returns:
            bool: True if network is available
        """
        self._retry = True
        try:
            session = requests.Session()
            session.trust_env = False
            _ = session.get('https://www.baidu.com', timeout=5)
            network_available = True
        except Exception as e:
            logger.error(e)
            network_available = False

        logger.attr('network_available', network_available)
        if network_available:
            logger.info('Trigger fast retry.')
            last = self._state.copy()
            for _ in range(3):
                logger.info(f'Retry {_ + 1} times ...')
                self._load_server()
                if self._state[0]:
                    self._retry = False
                    self._state.extend(last)
                    return True

            logger.error('Cannot connect to API. Please check you network or disable server checker.')
            self._retry = False
            self._state.extend(last)
            return False
        else:
            self._retry = False
            logger.error('Network is unavailable. Please check your network status.')
            return False
