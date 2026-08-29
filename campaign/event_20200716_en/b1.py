class Campaign(CampaignBase):
    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_potential_roadblocks([road_main]):
            return True
        return self.battle_default()
    def battle_5(self):
        self.fleet_boss.capture_clear_boss()
