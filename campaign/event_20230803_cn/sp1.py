class Campaign(CampaignBase):

    def battle_0(self):
        if self.map_is_clear_mode:
            if self.clear_siren():
                return True
            if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
                return True
        elif self.clear_any_enemy(sort=('cost_2',)):
            return True
        return self.battle_default()
