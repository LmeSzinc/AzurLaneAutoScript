class Campaign(CampaignBase):
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
    def battle_5(self):
        if not self.map_is_clear_mode:
            if self.clear_siren():
                return True
        return self.fleet_boss.clear_boss()
    def catch_camera_repositioning(self, destination):
        if super().catch_camera_repositioning(destination):
            return True
        if not self.map_is_clear_mode and destination.is_fortress:
            logger.info('Catch camera re-positioning after fortress cleared')
            self.device.sleep(3)
            return True
        return False
    def map_data_init(self, map_):
        self.config.MAP_HAS_FORTRESS = True
        super().map_data_init(map_)
    def handle_clear_mode_config_cover(self):
        self.map.fortress_data = [self.map.fortress_data[0], ()]
