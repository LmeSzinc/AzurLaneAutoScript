class Campaign(CampaignBase):
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
    def battle_5(self):
        return self.fleet_boss.clear_boss()
    def before_boss(self):
        logger.info('B2 before boss')
        grid = SelectedGrids([B6, C7]).sort('weight', 'cost')[0]
        self.fleet_boss.goto(grid)
        self.fleet_boss.goto(B8)
    def clear_boss(self):
        self.before_boss()
        super().clear_boss()
    def brute_clear_boss(self):
        self.before_boss()
        super().brute_clear_boss()
