class Campaign(CampaignBase):
    def battle_0(self):
        if self.clear_siren():
            return True
        return self.battle_clear_roadblocks(road_main, potential=True)
    def battle_4(self):
        self.fleet_boss.capture_clear_boss()
