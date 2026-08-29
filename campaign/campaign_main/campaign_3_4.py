class Campaign(CampaignBase):
    def battle_0(self):
        self.fleet_2_push_forward()
        if self.fleet_2_rescue(H3):
            return True
        return self.battle_default()
    def battle_3(self):
        if not self.check_accessibility(H3, fleet='boss'):
            return self.battle_default()
        return self.fleet_boss.clear_boss()
