class Campaign(CampaignBase):
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    def handle_clear_mode_config_cover(self):
        super().handle_clear_mode_config_cover()
        self.config.MAP_HAS_MISSILE_ATTACK = False
    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
    def battle_4(self):
        return self.clear_boss()
