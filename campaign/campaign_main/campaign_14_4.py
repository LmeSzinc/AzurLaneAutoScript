class Campaign(CampaignBase):
    def map_data_init(self, map_):
        super().map_data_init(map_)
        if not self.map_is_clear_mode:
            for override_grid in OVERRIDE:
                self.map[override_grid.location].may_enemy = override_grid.may_enemy
    def battle_0(self):
        self.pick_up_light_house(A9)
        if self.clear_roadblocks([road_A8, road_H9], weakest=False):
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True
        return self.battle_default()
    def battle_3(self):
        self.pick_up_light_house(A9)
        self.pick_up_ammo()
        self.pick_up_flare(H9)
        if self.clear_roadblocks([road_A8, road_H9], weakest=False):
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True
        return self.battle_default()
    def battle_6(self):
        self.pick_up_light_house(A9)
        self.pick_up_ammo()
        self.pick_up_flare(H9)
        if self.clear_roadblocks([road_A8, road_H9], weakest=False):
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
    def battle_7(self):
        self.fleet_boss.pick_up_flare(A5)
        return self.fleet_boss.clear_boss()
