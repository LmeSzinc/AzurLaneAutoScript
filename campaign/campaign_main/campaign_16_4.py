class Campaign(CampaignBase):
    F5_is_moved = False
    use_single_fleet = False
    def map_init(self, map_):
        super().map_init(map_)
        self.F5_is_moved = False
        self.map_has_mob_move = self.use_support_fleet and self.map_is_clear_mode
        self.use_single_fleet = 'standby' in self.config.Fleet_FleetOrder
    def battle_0(self):
        if self.map_has_mob_move and (not self.use_single_fleet):
            if self.mob_move(D7, D8):
                self.fleet_boss.goto(J1)
                self.fleet_ensure(index=3 - self.fleet_boss_index)
                if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
                    return True
                return self.battle_default()
            self.map_has_mob_move = False
        return self.clear_chosen_enemy(D5)
    def battle_1(self):
        if not self.map_has_mob_move:
            return self.clear_chosen_enemy(F5)
        if not self.use_single_fleet:
            if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
                return True
            return self.battle_default()
        grids = SelectedGrids([H6, I5])
        grid = grids.delete(grids.select(enemy_genre='Main')).first_or_none()
        if grid is not None and self.mob_move(F5, F6):
            self.F5_is_moved = True
            return self.clear_chosen_enemy(grid)
        self.F5_is_moved = False
        return self.clear_chosen_enemy(F5)
    def battle_2(self):
        if not self.map_has_mob_move or self.use_single_fleet:
            return self.clear_chosen_enemy(G4)
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
    def battle_3(self):
        if not self.map_has_mob_move:
            return self.clear_chosen_enemy(H3)
        if not self.use_single_fleet:
            if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
                return True
            return self.battle_default()
        if self.F5_is_moved:
            if I6.enemy_genre == 'Main' and self.mob_move(I6, I7):
                return self.clear_any_enemy(genre=('Light',), strongest=True)
            return self.clear_chosen_enemy(I6)
        self.mob_move(H3, I3)
        self.mob_move(I3, I2)
        return self.clear_any_enemy(genre=('Light',), strongest=True)
    def battle_4(self):
        if self.map_is_clear_mode:
            return self.fleet_boss.clear_boss()
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                return self.clear_roadblocks([road_main])
            if self.use_support_fleet:
                self.goto(J6)
                self.air_strike(I8)
            return self.fleet_boss.clear_boss()
        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_potential_roadblocks([road_main]):
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
