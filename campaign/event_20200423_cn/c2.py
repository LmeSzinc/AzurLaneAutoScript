class Campaign(CampaignBase):
    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_enemy(scale=(1, 2)):
            return True
        return self.battle_default()
    def battle_4(self):
        return self.brute_clear_boss()
