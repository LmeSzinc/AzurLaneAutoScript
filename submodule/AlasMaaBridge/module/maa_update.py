import pathlib

import requests

from module.logger import logger
from submodule.AlasMaaBridge.module.asst.updater import Updater


def maa_update(self):
    path = pathlib.Path(self.config.MaaEmulator_MaaPath)
    if self.config.MaaUpdates_UpdateCore is True:
        Updater(path, self.config.MaaUpdates_UpdateChannel).update()
    if self.config.MaaUpdates_UpdateResource is True:
        ota_tasks_url = 'https://ota.maa.plus/MaaAssistantArknights/api/resource/tasks.json'
        ota_tasks_path = path / 'cache' / 'resource' / 'tasks.json'
        ota_tasks_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ota_tasks_path, 'w', encoding='utf-8') as f:
            session = requests.Session()
            session.trust_env = False
            response = session.get(ota_tasks_url)
            f.write(response.text)
        logger.info(f'MAA资源更新成功：{ota_tasks_path}')
