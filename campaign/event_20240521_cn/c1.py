class Campaign(CampaignBase):
    grid_class = CurrentFleetGrid
    bored_visited_G3 = False
    bored_visited_H2 = False

    def find_current_fleet(self):
        logger.hr('Find current fleet')
        logger.info('No fleet scan, assume fleet_1 at D5')
        self.fleet_1 = D5.location
        if self.config.FLEET_2:
            logger.info('No fleet scan, assume fleet_2 at F5')
            self.fleet_2 = F5.location

    def map_init(self, map_):
        super().map_init(map_)
        self.bored_visited_G3 = False
        self.bored_visited_H2 = False
        self.config.FLEET_BOSS = 1

    def bored_visit(self):
        if not self.bored_visited_G3:
            self.bored_visited_G3 = True
            if self.clear_chosen_enemy(G3):
                return True
        if not self.bored_visited_H2:
            self.bored_visited_H2 = True
            if self.clear_chosen_enemy(H2):
                return True
        return False

    def battle_function(self):
        if self.battle_count == 0:
            return self.battle_0()
        if self.config.MAP_CLEAR_ALL_THIS_TIME:
            remain = self.map.select(is_enemy=True).add(self.map.select(is_siren=True)).add(self.map.select(is_fortress=True)).delete(self.map.select(is_boss=True))
            logger.info(f'Enemy remain: {remain}')
            logger.info(f'bored_visited_G3: {self.bored_visited_G3}, bored_visited_H2: {self.bored_visited_H2}')
            if remain.count > 0:
                if self.clear_siren():
                    return True
                self.clear_mechanism()
                return self.battle_default()
            else:
                if self.bored_visit():
                    return True
                result = self.battle_boss()
                return result
        else:
            return super().battle_function()

    def battle_0(self):
        if self.fleet_step >= 3:
            if self.clear_chosen_enemy(E7, expected='siren'):
                return True
        else:
            self.goto(E6)
            if self.clear_chosen_enemy(E7, expected='siren'):
                return True
        logger.warning(f'A1.battle_0() did not cleared siren')
        return self.battle_default()
