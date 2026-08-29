class Campaign(CampaignBase):
    def battle_0(self):
        self.fleet_2_push_forward()
        if self.fleet_2_rescue(H1):
            return True
        self.clear_all_mystery()
        return self.battle_default()
    def battle_3(self):
        self.clear_all_mystery()
        if not self.check_accessibility(H1, fleet='boss'):
            return self.battle_default()
        return self.fleet_boss.clear_boss()
