class Campaign(CampaignBase):

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
