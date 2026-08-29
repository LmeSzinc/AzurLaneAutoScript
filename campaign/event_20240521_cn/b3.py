class Campaign(CampaignBase):
    grid_class = CurrentFleetGrid
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    def in_sight(self, location, sight=None):
        logger.info('In sight: %s' % location2node(location))
        x, y = location
        if x >= 7 and y <= 4:
            x = 7
            location = (x, y)
            logger.info('In sight: %s' % location2node(location))
            return super().focus_to(location)
        if x <= 4 and y <= 4:
            x = 3
            location = (x, y)
            logger.info('In sight: %s' % location2node(location))
            return super().focus_to(location)
        return super().in_sight(location, sight=sight)
    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
    def battle_5(self):
        return self.fleet_boss.clear_boss()
