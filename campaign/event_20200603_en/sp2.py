class Campaign(CampaignBase):
    def battle_0(self):
        self.clear_all_mystery()
        return self.battle_default()
    def battle_1(self):
        return self.battle_default()
    def battle_4(self):
        return self.brute_clear_boss()
