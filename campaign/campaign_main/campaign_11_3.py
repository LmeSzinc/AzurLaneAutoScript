class Campaign(CampaignBase):
    def battle_0(self):
        return self.battle_clear_roadblocks(road_main, potential=True)
    def battle_6(self):
        if self.clear_roadblocks([road_main]):
            return True
        return self.fleet_boss.clear_boss()
