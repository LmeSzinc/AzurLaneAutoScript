class Campaign(CampaignBase):

    def battle_6(self):
        self.clear_map_items([F1, I1])
        return self.fleet_boss.clear_boss()
