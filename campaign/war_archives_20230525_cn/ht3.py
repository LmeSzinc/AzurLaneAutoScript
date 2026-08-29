class Campaign(CampaignBase):
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    def battle_0(self):
        if self.map_is_clear_mode:
            if self.clear_siren():
                return True
            if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
                return True
        else:
            if self.clear_siren():
                return True
            if self.clear_any_enemy(sort=('cost_2',)):
                return True
        return self.battle_default()
    def battle_5(self):
        return self.fleet_boss.clear_boss()
    def combat_status(self, *args, **kwargs):
        if not self.map_is_clear_mode and self.battle_count >= 5:
            self.device.disable_stuck_detection()
        super().combat_status(*args, **kwargs)
