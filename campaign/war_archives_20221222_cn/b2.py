class Campaign(CampaignBase):
    ENEMY_FILTER = '1L > 1M > 2L > 2M > 3L > 3M > 1E > 2E > 3E > 1C > 2C > 3C'
    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
    def battle_5(self):
        return self.fleet_boss.clear_boss()
