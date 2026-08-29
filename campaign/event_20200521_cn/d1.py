class Campaign(CampaignBase):
    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_enemy(scale=(1,)):
            return True
        if self.clear_enemy(scale=(2,), genre=['light', 'main', 'enemy', 'carrier']):
            return True
        if self.clear_enemy(genre=['light', 'main']):
            return True
        return self.battle_default()
    def battle_5(self):
        return self.fleet_boss.brute_clear_boss()
