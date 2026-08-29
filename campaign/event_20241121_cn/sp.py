class Campaign(CampaignBase):
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    def map_data_init(self, map_):
        super().map_data_init(map_)
        D5.is_siren = True
        E4.is_siren = True
        E6.is_siren = True
    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=2):
            return True
        return self.battle_default()
    def battle_5(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
    def battle_7(self):
        return self.fleet_boss.clear_boss()
