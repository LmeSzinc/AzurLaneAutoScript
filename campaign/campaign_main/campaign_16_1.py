class Campaign(CampaignBase):

    def battle_5(self):
        boss = self.map.select(is_boss=True)
        if boss:
            return self.fleet_boss.clear_boss()
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
