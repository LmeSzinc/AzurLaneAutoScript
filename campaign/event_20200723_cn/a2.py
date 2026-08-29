class Campaign(CampaignBase):
    def battle_0(self):
        if self.clear_siren():
            return True
        return self.battle_default()
    def battle_4(self):
        return self.fleet_boss.clear_boss()
