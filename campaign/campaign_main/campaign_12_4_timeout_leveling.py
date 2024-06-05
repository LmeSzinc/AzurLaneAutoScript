from module.campaign.campaign_base import CampaignBase
from module.combat.assets import *
from module.logger import logger
from module.map.map_base import CampaignMap
from module.map.map_grids import RoadGrids, SelectedGrids


class Campaign(CampaignBase):
    # MAP = MAP

    def battle_default(self):
        if not self.map.select(enemy_scale=3, enemy_genre='Light'):
            self.withdraw()

    def handle_combat_weapon_release(self):
        if self.appear_then_click(READY_AIR_RAID, interval=5):
            return True

        return False

    def handle_battle_status(self, save_get_items=False):
        """
        Args:
            save_get_items (bool):

        Returns:
            bool:
        """
        if self.is_combat_executing():
            return False
        if self.appear_then_click(BATTLE_STATUS_S, screenshot=save_get_items, genre='status', interval=self.battle_status_click_interval):
            if not save_get_items:
                self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(BATTLE_STATUS_A, screenshot=save_get_items, genre='status', interval=self.battle_status_click_interval):
            logger.warning('Battle status: A')
            if not save_get_items:
                self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(BATTLE_STATUS_B, screenshot=save_get_items, genre='status', interval=self.battle_status_click_interval):
            logger.warning('Battle Status B')
            if not save_get_items:
                self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(BATTLE_STATUS_C, screenshot=save_get_items, genre='status', interval=self.battle_status_click_interval):
            if not save_get_items:
                self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(BATTLE_STATUS_D, screenshot=save_get_items, genre='status', interval=self.battle_status_click_interval):
            logger.warning('Battle Status D')
            if not save_get_items:
                self.device.sleep((0.25, 0.5))
            return True

        return False

    def handle_get_items(self, save_get_items=False):
        """
        Args:
            save_get_items (bool):

        Returns:
            bool:
        """
        if self.appear_then_click(GET_ITEMS_1, screenshot=save_get_items, genre='get_items', offset=5,
                                  interval=self.battle_status_click_interval):
            self.interval_reset(BATTLE_STATUS_S)
            self.interval_reset(BATTLE_STATUS_A)
            self.interval_reset(BATTLE_STATUS_B)
            self.interval_reset(BATTLE_STATUS_C)
            self.interval_reset(BATTLE_STATUS_D)
            return True
        if self.appear_then_click(GET_ITEMS_2, screenshot=save_get_items, genre='get_items', offset=5,
                                  interval=self.battle_status_click_interval):
            self.interval_reset(BATTLE_STATUS_S)
            self.interval_reset(BATTLE_STATUS_A)
            self.interval_reset(BATTLE_STATUS_B)
            self.interval_reset(BATTLE_STATUS_C)
            self.interval_reset(BATTLE_STATUS_D)
            return True

        return False

    def handle_exp_info(self):
        """
        Returns:
            bool:
        """
        if self.is_combat_executing():
            return False
        if self.appear_then_click(EXP_INFO_S):
            self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(EXP_INFO_A):
            self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(EXP_INFO_B):
            self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(EXP_INFO_C):
            self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(EXP_INFO_D):
            self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(OPTS_INFO_D, offset=(20, 20)):
            self.device.sleep((0.25, 0.5))
            return True

        return False

    def combat(self, balance_hp=None, emotion_reduce=None, func=None, call_submarine_at_boss=None, save_get_items=None,
               expected_end=None, fleet_index=1):
        self.battle_status_click_interval = 7 if save_get_items else 0
        super().combat(balance_hp=False, expected_end='no_searching', auto_mode='hide_in_bottom_left', save_get_items=False)


from module.config.config import AzurLaneConfig

az = Campaign(AzurLaneConfig('alas'))
for n in range(10000):
    logger.hr(f'count: {n}')
    az.map_offensive()
    az.combat()
