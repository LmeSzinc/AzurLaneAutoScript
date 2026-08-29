class Campaign(CampaignBase):

    def battle_3(self):
        self.clear_all_mystery()
        if not self.check_accessibility(D1, fleet='boss'):
            return self.battle_default()
        return self.fleet_boss.clear_boss()
