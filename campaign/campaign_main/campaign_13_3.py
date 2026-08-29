class Campaign(CampaignBase):
    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy('1L > 1M > 2L > 2M > 3L > 2E > 3E > 2C > 3C > 3M', preserve=1):
            return True
        return self.battle_default()
    def battle_5(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy('1L > 1M > 2L > 2M > 3L > 2E > 3E > 2C > 3C > 3M', preserve=0):
            return True
        return self.battle_default()
    def battle_6(self):
        return self.fleet_boss.clear_boss()
