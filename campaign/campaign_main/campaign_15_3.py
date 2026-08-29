class Campaign(CampaignBase):

    def battle_function(self):
        if not self.config.MAP_CLEAR_ALL_THIS_TIME:
            return super().battle_function()
        if self.battle_count == 3 or (self.battle_count == 0 and (not self.map_is_clear_mode)):
            func = self.FUNCTION_NAME_BASE + str(self.battle_count)
            logger.info(f'Using function: {func}')
            func = self.__getattribute__(func)
            result = func()
            return result
        return super().battle_function()

    def battle_0(self):
        if not self.map_is_clear_mode and self.map_has_mob_move:
            self.mob_move(B3, B4)
            if A1.is_accessible:
                self.clear_chosen_enemy(A1)
                return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True
        return self.battle_default()

    def battle_3(self):
        self.clear_chosen_enemy(H5, expected='siren')
        return True
