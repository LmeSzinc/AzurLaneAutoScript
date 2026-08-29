class Campaign(CampaignBase):
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    def battle_0(self):
        self.fleet_2_push_forward()
        return self.battle_clear_roadblocks(ROAD_MAIN, potential=True)
    def battle_6(self):
        self.clear_all_mystery()
        return self.fleet_boss.clear_boss()
