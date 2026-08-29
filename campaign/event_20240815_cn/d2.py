class Campaign(CampaignBase):

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
