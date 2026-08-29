class Campaign(CampaignBase):
    def battle_0(self):
        return self.battle_default()
    def battle_1(self):
        return self.clear_boss()
    def handle_boss_appear_refocus(self, preset=(-3, 0)):
        return super().handle_boss_appear_refocus(preset)
