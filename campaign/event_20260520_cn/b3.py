class Campaign(CampaignBase):
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    grid_class = GridCurrentFleet
    def in_sight(self, location, sight=None):
        location = location_ensure(location)
        node = location2node(location)
        if node == 'E3':
            return self.focus_to('E3')
        return super().in_sight(location, sight=sight)
    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
    def battle_5(self):
        return self.fleet_boss.clear_boss()
