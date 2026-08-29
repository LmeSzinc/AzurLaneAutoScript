class Campaign(CampaignBase):
    def battle_0(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True
        return self.battle_default()
    def battle_5(self):
        boss = self.map.select(is_boss=True)
        if boss:
            return self.fleet_boss.clear_boss()
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
    def battle_6(self):
        return self.fleet_boss.clear_boss()
