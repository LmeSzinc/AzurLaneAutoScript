from ..campaign_war_archives.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger


class CampaignBase(CampaignBase_):
    STAGE_INCREASE = [
        'A1 > A2 > A3',
        'B1 > B2 > BS1 > B3',
        'C1 > C2 > C3',
        'D1 > D2 > DS1 > D3',
        'SP1 > SP2 > SP3 > SP4',
        'T1 > T2 > T3 > T4',
    ]

    def handle_clear_mode_config_cover(self):
        super().handle_clear_mode_config_cover()
        self.config.MAP_HAS_MISSILE_ATTACK = True

    def round_battle(self, after_battle=True):
        """
        Call this method after cleared an enemy.
        """
        super().round_battle()
        # new = {0: 0}
        # for spawn_round, count in self.enemy_round.items():
        #     new[0] += count
        # if after_battle:
        #     new[0] = max(new[0] - 1, 0)
        # self.enemy_round = new
        # from module.logger import logger
        logger.info(f'Enemy round: {self.enemy_round}')
