class Campaign(CampaignBase):

    def battle_0(self):
        if self.config.MAP_HAS_MOVABLE_ENEMY:
            self.fleet_2_push_forward()
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
