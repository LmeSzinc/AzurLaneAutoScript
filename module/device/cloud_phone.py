import json
import time
from datetime import datetime, timedelta

from module.config.utils import get_server_next_update
from module.device.chinac_api import ChinacOpenApi
from module.exception import RequestHumanTakeover
from module.handler.login import LoginHandler
from module.logger import logger


class CloudPhoneManager(LoginHandler):
    def __init__(self, config, device):
        super().__init__(config, device)
        self.api = ChinacOpenApi(self.config.RestartChinacCloudPhone_AccessKey,
                                 self.config.RestartChinacCloudPhone_AccessKeySecret)
        self.region = self.config.RestartChinacCloudPhone_CloudPhoneRegion
        self.id = self.config.RestartChinacCloudPhone_CloudPhoneID

    def _get_status(self):
        #  START：运行中；STOP：已关闭；ERROR：异常；CREATING：创建中；STARTING：开机中；
        #  STOPING：关机中；PAUSING：暂停中；PAUSED：已暂停；UNPAUSING：取消暂停
        #  REBOOTING：重启中；RESIZE：变更中；MIGRATE：迁移中；
        self.api.set_action('DescribeCloudPhone')
        self.api.set_http_method('POST')
        self.api.set_request_params({'Region': self.region, 'Id': self.id})
        try:
            result = self.api.do()
            res = json.loads(result['Info'])
            logger.info(f'Cloud phone status: {res["data"]["BasicInfo"]["Status"]}')
            return res['data']['BasicInfo']['Status']
        except Exception as e:
            logger.warning(f'Failed to get cloud phone status: {e}')
            return

    def _restart(self):
        self.api.set_action('RebootCloudPhone')
        self.api.set_http_method('POST')
        self.api.set_request_params({'Operate': "reboot", 'CloudPhones': [{'Region': self.region, 'Id': self.id}]})
        return self.api.do()

    def _wait_for_status(self, status: str, timeout: int = 180):
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_status = self._get_status()
            if current_status == status:
                return
            else:
                time.sleep(10)
        raise TimeoutError(f'Failed to wait for status {status} in {timeout} seconds')

    def _can_execute(self) -> bool:
        """
        Determine whether the task should be executed.
        Principle:
            * Basically execute on every 6 hours.
            * Only execute when there is no pending tasks.
            * Avoid execute when there is less than 5 minutes before the next task.
            * At least restart once a day.
        """
        if get_server_next_update("00:00") - datetime.now() < timedelta(hours=6):
            # at least restart once a day before server update
            return True
        self.config.get_next_task()
        if len(self.config.pending_task) > 1:
            logger.info('Delay when there is pending tasks')
            self.config.task_delay(minute=30)
            return False
        if self.config.waiting_task:
            tast = self.config.waiting_task[0]
            if tast.next_run - datetime.now() > timedelta(minutes=5):
                logger.info('Have enough time to execute')
                return True
            else:
                logger.info('Delay for no enough time to execute')
                self.config.task_delay(minute=30)
                return False

    def restart(self):
        logger.hr('Restart cloud phone')
        if not self._can_execute():
            return
        try:
            self._restart()
            self._wait_for_status('REBOOTING')
            self._wait_for_status('START')
            logger.info('Restart cloud phone successfully')
        except Exception as e:
            logger.warning(e)
            self.config.Scheduler_Enable = False
            return
        wait = 5
        for _ in range(5):
            # Can't start app immediately after restart
            time.sleep(wait)
            try:
                self.device.app_stop()
                self.device.app_start()
                self.handle_app_login()
                self.config.task_delay(minute=360)
                return
            except Exception as e:
                logger.warning(e)
                logger.info("Cloud phone just start, wait and retry")
                wait += 5
                continue
        raise RequestHumanTakeover('Failed to start app after restart cloud phone')
