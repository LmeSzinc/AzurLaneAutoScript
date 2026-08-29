class Campaign(CampaignBase):

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
