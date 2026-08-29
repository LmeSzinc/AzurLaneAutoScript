class Campaign(CampaignBase):
    def battle_0(self):
        return self.battle_default()
    def battle_5(self):
        return self.fleet_boss.clear_boss()
