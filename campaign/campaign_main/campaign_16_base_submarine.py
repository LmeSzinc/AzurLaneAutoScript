from module.logger import logger

from .campaign_support_fleet import CampaignBase as CampaignBase_


class Config:
    MAP_WALK_TURNING_OPTIMIZE = False
    MAP_HAS_MYSTERY = False
    HOMO_EDGE_COLOR_RANGE = (0, 12)
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 210


class CampaignBase(CampaignBase_):
    ENEMY_FILTER = '1T > 1L > 1E > 1M > 2T > 2L > 2E > 2M > 3T > 3L > 3E > 3M'

    def map_init(self, map_):
        if self.use_support_fleet:
            logger.hr(f'{self.FUNCTION_NAME_BASE}SUBMARINE', level=2)
            self.combat(balance_hp=False, emotion_reduce=False, save_get_items=False)
        super().map_init(map_)

    def handle_submarine_support_popup(self):
        if self.use_support_fleet and self.handle_popup_confirm("SUBMARINE_SUPPORT"):
            return True
        return False
