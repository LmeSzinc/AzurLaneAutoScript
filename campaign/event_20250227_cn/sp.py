class Campaign(CampaignBase):
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
