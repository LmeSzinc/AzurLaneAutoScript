class Campaign(CampaignBase):
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def handle_clear_mode_config_cover(self):
        super().handle_clear_mode_config_cover()
        self.config.MAP_HAS_MISSILE_ATTACK = False
