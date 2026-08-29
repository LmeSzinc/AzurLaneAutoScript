class Campaign(CampaignBase):

    def battle_6(self):
        self.clear_map_items([E2, E7])
        return self.fleet_boss.clear_boss()
