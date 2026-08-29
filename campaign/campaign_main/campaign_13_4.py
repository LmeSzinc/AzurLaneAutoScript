class Campaign(CampaignBase):
    def battle_0(self):
        if self.clear_filter_enemy('1L > 1M > 2L > 2M > 3L > 2E > 3E > 2C > 3C > 3M', preserve=0):
            return True
        return self.battle_default()
    def battle_3(self):
        self.pick_up_ammo()
        if self.clear_filter_enemy('1L > 1M > 2L > 2M > 3L > 2E > 3E > 2C > 3C > 3M', preserve=0):
            return True
        return self.battle_default()
    def battle_7(self):
        return self.fleet_boss.clear_boss()
