class Campaign(CampaignBase):
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
