from module.base.base import ModuleBase
from module.logger import logger
from module.config.utils import filepath_config, write_file


class Backup(ModuleBase):
    def run(self):
        logger.hr('Backup')
        logger.info(f'The config will be backed up in ./config/{self.config.config_name}.json.bak')
        write_file(filepath_config(self.config.config_name) + '.bak', data=self.config.data)
        self.config.task_delay(success=True)
