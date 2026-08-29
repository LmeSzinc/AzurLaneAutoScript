class Campaign(CampaignBase):
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    def battle_0(self):
        if self.map_is_clear_mode:
            if self.clear_siren():
                return True
            if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
                return True
        elif self.clear_any_enemy(sort=('cost_2',)):
            return True
        return self.battle_default()
    def battle_3(self):
        return self.clear_boss()
