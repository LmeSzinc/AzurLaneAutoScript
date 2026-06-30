from typing import List

from ..campaign_war_archives.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger
from module.map_detection.grid import GridInfo


class CampaignBase(CampaignBase_):
    MACHINE_FORTRESS: List[GridInfo]

    # def handle_clear_mode_config_cover(self):
    #     if super().handle_clear_mode_config_cover():
    #         logger.info(f'No machine fortress in clear mode')
    #         return True
    #     else:
    #         if hasattr(self, 'MACHINE_FORTRESS'):
    #             logger.info(f'Set machine fortress: {self.MACHINE_FORTRESS}')
    #             for grid in self.MACHINE_FORTRESS:
    #                 grid.manual_siren = True
    #         else:
    #             logger.info(f'No machine fortress in this stage')
    #             return False
