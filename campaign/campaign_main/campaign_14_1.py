class Campaign(CampaignBase):
    def battle_0(self):
        self.pick_up_light_house(E3)
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True
        return self.battle_default()
    def battle_5(self):
        self.pick_up_light_house(E3)
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
    def battle_6(self):
        self.fleet_boss.pick_up_flare(C5)
        return self.fleet_boss.clear_boss()
