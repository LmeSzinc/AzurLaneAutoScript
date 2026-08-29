class Campaign(CampaignBase):
    grid_class = EventGrid
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

    def battle_0(self):
        if self.fleet_2_push_forward():
            return True
        return self.battle_default()
