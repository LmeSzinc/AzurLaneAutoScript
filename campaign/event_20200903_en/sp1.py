class Campaign(CampaignBase):
    def battle_0(self):
        if self.clear_siren():
            return True
        self.clear_mechanism()
        if self.clear_roadblocks([road_main]):
            return True
        return self.battle_default()
    def battle_4(self):
        return self.clear_boss()
