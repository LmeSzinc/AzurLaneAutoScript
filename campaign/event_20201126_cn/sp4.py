class Campaign(CampaignBase):

    def battle_0(self):
        if self.fleet_2_protect():
            return True
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
