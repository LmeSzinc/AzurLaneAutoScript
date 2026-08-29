class Campaign(CampaignBase):
    use_single_fleet = False
    def map_init(self, map_):
        super().map_init(map_)
        self.map_has_mob_move = self.use_support_fleet and self.map_is_clear_mode
        self.use_single_fleet = 'standby' in self.config.Fleet_FleetOrder
    def battle_0(self):
        if self.map_has_mob_move:
            if self.mob_move(C3, C2):
                return self.clear_chosen_enemy(D6)
            self.map_has_mob_move = False
        return self.clear_chosen_enemy(C3)
    def battle_1(self):
        if self.map_has_mob_move:
            self.mob_move(E6, E5)
            if not self.use_single_fleet:
                self.fleet_boss.goto(F4)
                self.fleet_ensure(index=3 - self.fleet_boss_index)
            return self.clear_chosen_enemy(G4)
        if self.use_support_fleet and (not self.map_is_clear_mode):
            self.goto(C3)
            self.air_strike(E3)
        return self.clear_chosen_enemy(D3)
    def battle_2(self):
        return self.clear_chosen_enemy(F3)
    def battle_3(self):
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                return self.clear_roadblocks([road_main])
            if self.use_support_fleet and (not self.map_is_clear_mode):
                self.goto(K5)
                self.air_strike(J6)
            return self.fleet_boss.clear_boss()
        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_any_enemy(genre=('Light',), strongest=True):
            return True
        return self.battle_default()
