class Campaign(CampaignBase):

    def battle_0(self):
        if self.clear_siren():
            return True
        self.clear_mechanism()
        return self.battle_clear_roadblocks(road_main)
