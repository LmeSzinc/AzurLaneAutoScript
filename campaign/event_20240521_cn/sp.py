class Campaign(CampaignBase):
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    is_left = False
    def map_data_init(self, map_):
        super().map_data_init(map_)
        B7.is_siren = True
        C8.is_siren = True
        D7.is_siren = True
    def battle_0(self):
        self.is_left = self.fleet_current == B10.location
        logger.attr('is_left', self.is_left)
        self.goto(C9)
        self.clear_chosen_enemy(C8, expected='siren')
        return True
    def battle_1(self):
        if self.is_left:
            self.clear_chosen_enemy(D9, expected='siren')
            return True
        else:
            self.clear_chosen_enemy(B9, expected='siren')
            return True
    def battle_2(self):
        if self.is_left:
            self.clear_chosen_enemy(B9, expected='siren')
            return True
        else:
            self.clear_chosen_enemy(D9, expected='siren')
            return True
    def battle_3(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=2):
            return True
        return self.battle_default()
    def battle_5(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
    def battle_7(self):
        return self.fleet_boss.clear_boss()
