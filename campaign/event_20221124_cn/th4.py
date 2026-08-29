class Campaign(CampaignBase):

    def battle_6(self):
        self.clear_map_items([G5, I2])
        return self.fleet_boss.clear_boss()
