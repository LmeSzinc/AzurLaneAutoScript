class Campaign(CampaignBase):
    def battle_0(self):
        if self.clear_siren():
            return True
        return self.battle_default()
    def battle_3(self):
        return self.fleet_1.clear_boss()
