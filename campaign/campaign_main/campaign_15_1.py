class Campaign(CampaignBase):

    def battle_function(self):
        if self.config.MAP_CLEAR_ALL_THIS_TIME and self.battle_count == 0 and (not self.map_is_clear_mode):
            func = self.FUNCTION_NAME_BASE + str(self.battle_count)
            logger.info(f'Using function: {func}')
            func = self.__getattribute__(func)
            result = func()
            return result
        return super().battle_function()

    def battle_0(self):
        if not self.map_is_clear_mode and self.map_has_mob_move:
            self.mob_move(B3, C3)
            if B1.is_accessible:
                self.clear_chosen_enemy(B1)
                return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True
        return self.battle_default()
