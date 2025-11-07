import module.config.server as server

from module.island.assets import *
from module.island.project_data import *
from module.island.project import IslandProjectRun
from module.island.transport import IslandTransportRun
from module.logger import logger
from module.ui.page import page_dormmenu, page_island, page_island_phone, page_main


class Island(IslandProjectRun, IslandTransportRun):
    @staticmethod
    def island_config_to_names(config):
        """
        Args:
            config (list[bool]): list of config for island receive
        
        Returns:
            list[str]: a list of name for island receive
        """
        if any(config):
            return [name for add, name in zip(config, list(name_to_slot_cn.keys())) if add]
        else:
            return []

    def island_run(self, transport=True, project=True, names=None):
        """
        Execute island routine.

        Args:
            transport (bool):
            project (bool):
            names (list[str]): a list of name for island receive
        """
        future_finish = []
        if transport:
            if self.island_transport_enter():
                future_finish.extend(self.island_transport_run())
                self.island_ui_back()

        if project:
            if self.island_management_enter():
                future_finish.extend(self.island_project_run(names=names))
                self.island_ui_back()
            else:
                logger.warning('Island management locked, please reach island level 18 '
                                'and unlock island management to use this task.')
                self.config.Scheduler_Enable = False
                return False

        # task delay
        if len(future_finish):
            self.config.task_delay(target=future_finish)
        else:
            logger.info('No island routine running')
            self.config.task_delay(success=False)

    def run(self):
        if server.server in ['cn']:
            transport = False
            project_config = [self.config.__getattribute__(f'Island{i}_Receive') for i in range(1, 16)]
            project = any(project_config)
            names = self.island_config_to_names(project_config)
            if transport or project:
                self.ui_goto_island()
                self.ui_ensure(page_island_phone)
                self.island_run(transport=transport, project=project, names=names)
                self.ui_goto(page_main, get_ship=False)
            else:
                logger.info('Nothing to receive, skip island running')
                self.config.task_delay(server_update=True)
        else:
            logger.info(f'Island task not presently supported for {server.server} server.')
            logger.info('If want to address, review necessary assets, replace, update above condition, and test')
            self.config.task_delay(server_update=True)
