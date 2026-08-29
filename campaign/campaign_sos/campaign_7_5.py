class Campaign(CampaignBase):

    def battle_0(self):
        if self.fleet_2_push_forward():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True
        return self.battle_default()
