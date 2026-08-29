class Campaign(CampaignBase):
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    def battle_function(self):
        if self.config.MAP_CLEAR_ALL_THIS_TIME:
            remain = self.map.select(is_enemy=True)
            logger.info(f'Enemy remain: {remain}')
            if remain:
                if self.fleet_2_protect():
                    return True
                elif self.clear_any_enemy(sort=('weight', 'cost_2', 'cost_1')):
                    return True
        if not self.map_is_clear_mode:
            remain = self.map.select(is_enemy=True)
            logger.info(f'Enemy remain: {remain}')
            boss = self.map.select(is_boss=True)
            logger.info(f'Boss appear: {boss}')
            if not boss:
                if self.fleet_2_protect():
                    return True
                elif self.clear_any_enemy(sort=('weight', 'cost_2', 'cost_1')):
                    return True
        return super().battle_function()
    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True
        return self.battle_default()
    def battle_5(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
    def battle_6(self):
        return self.fleet_boss.clear_boss()
