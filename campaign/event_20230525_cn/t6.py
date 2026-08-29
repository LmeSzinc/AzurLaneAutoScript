class Campaign(CampaignBase):

    def battle_0(self):
        if self.map_is_clear_mode:
            if self.clear_siren():
                return True
            if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
                return True
        elif self.clear_any_enemy(sort=('cost_2',)):
            return True
        return self.battle_default()

    def combat_status(self, *args, **kwargs):
        if not self.map_is_clear_mode and self.battle_count >= 5:
            self.device.disable_stuck_detection()
        super().combat_status(*args, **kwargs)
