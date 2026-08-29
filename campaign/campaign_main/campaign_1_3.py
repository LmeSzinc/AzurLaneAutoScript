class Campaign(CampaignBase):
    def battle_0(self):
        self.clear_all_mystery()
        return self.battle_default()
    def battle_2(self):
        self.clear_all_mystery()
        return self.clear_boss()
