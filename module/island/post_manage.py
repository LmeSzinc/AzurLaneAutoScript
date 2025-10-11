import module.config.server as server
from module.base.timer import Timer
from module.logger import logger
from module.island.assets import *
from module.island.interact import IslandInteract
from module.ui.page import (
    page_dormmenu,
    page_island,
    page_island_management,
    page_island_postmanage,
)

class PostManage(IslandInteract):
    def run(self):
        """
        Pages:
            in: Any page
            out: page_main, may have info_bar
        """
        if server.server in ['jp']:
            self.ui_ensure(page_dormmenu)
            self.ui_goto(page_island_postmanage)
            self.handle_info_bar()
            self.process_harvests()
        else:
            logger.info(f'Island Post Manage task not presently supported for {server.server} server.')
            logger.info('If want to address, review necessary assets, replace, update above condition, and test')

        self.config.task_delay(server_update=True)

    def process_harvests(self):
        pass