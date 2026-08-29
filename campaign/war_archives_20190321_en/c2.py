class Campaign(CampaignBase):
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    def battle_0(self):
        self.fleet_2_push_forward()
        if self.clear_roadblocks([ROAD_MAIN], strongest=True):
            return True
        if self.clear_potential_roadblocks([ROAD_MAIN], strongest=True):
            return True
        return self.battle_default()
    def battle_6(self):
        self.clear_all_mystery()
        return self.fleet_boss.clear_boss()
