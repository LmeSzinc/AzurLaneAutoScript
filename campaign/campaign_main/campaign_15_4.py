class Campaign(CampaignBase):

    def battle_function(self):
        if not self.config.MAP_CLEAR_ALL_THIS_TIME:
            return super().battle_function()
        if self.battle_count in [3, 6] or (self.battle_count in [0, 1] and (not self.map_is_clear_mode)):
            func = self.FUNCTION_NAME_BASE + str(self.battle_count)
            logger.info(f'Using function: {func}')
            func = self.__getattribute__(func)
            result = func()
            return result
        return super().battle_function()

    def battle_0(self):
        if not self.map_is_clear_mode and self.map_has_mob_move:
            self.mob_move(J8, K8)
            if K9.is_accessible:
                self.clear_chosen_enemy(K9)
                return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()

    def battle_1(self):
        if not self.map_is_clear_mode:
            if A1.is_accessible:
                self.clear_chosen_enemy(A1)
                return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()

    def battle_3(self):
        if not self.map_is_clear_mode:
            self.fleet_boss.clear_chosen_enemy(H5, expected='siren')
            self.fleet_1.switch_to()
            return True
        else:
            self.pick_up_ammo()
            self.clear_chosen_enemy(H5, expected='siren')
            return True

    def battle_4(self):
        self.pick_up_ammo()
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()

    def battle_6(self):
        self.clear_chosen_enemy(D3, expected='siren')
        return True
