class Campaign(CampaignBase):
    def battle_0(self):
        self.clear_all_mystery()
        return self.battle_default()
    def battle_2(self):
        self.clear_all_mystery()
        if not self.check_accessibility(D4, fleet='boss'):
            return self.battle_default()
        return self.fleet_boss.clear_boss()
    def handle_boss_appear_refocus(self, preset=(0, -2)):
        return super().handle_boss_appear_refocus(preset)
