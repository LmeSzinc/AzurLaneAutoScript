class Campaign(CampaignBase):
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    _is_D9 = False
    def battle_0(self):
        if self.fleet_at(D9):
            self._is_D9 = True
        if self._is_D9:
            self.clear_chosen_enemy(D7)
        else:
            self.clear_chosen_enemy(F7)
        return True
    def battle_1(self):
        if self._is_D9:
            self.clear_chosen_enemy(F7)
        else:
            self.clear_chosen_enemy(D7)
        return True
    def battle_2(self):
        if self._is_D9:
            self.clear_chosen_enemy(D7)
        else:
            self.clear_chosen_enemy(F7)
        return True
    def battle_3(self):
        if self._is_D9:
            self.clear_chosen_enemy(F7)
        else:
            self.clear_chosen_enemy(D7)
        return True
    def battle_4(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=2):
            return True
        return self.battle_default()
    def battle_5(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
    def battle_7(self):
        return self.fleet_boss.clear_boss()
