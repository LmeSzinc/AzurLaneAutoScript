class Campaign(CampaignBase):
    _is_a2 = False

    def battle_0(self):
        if self.fleet_at(A2):
            self._is_a2 = True
        self.goto(B3)
        self.clear_chosen_enemy(C3)
        return True

    def battle_1(self):
        if self._is_a2:
            self.clear_chosen_enemy(B4)
        else:
            self.clear_chosen_enemy(B2)
        return True

    def battle_2(self):
        if self._is_a2:
            self.goto(C3)
            self.clear_chosen_enemy(D3)
        else:
            self.clear_chosen_enemy(D2)
        return True
