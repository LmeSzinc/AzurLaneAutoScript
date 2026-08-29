class Campaign(CampaignBase):
    def battle_0(self):
        if self.fleet_2_step_on(FLEET_2_STEP_ON, roadblocks=[ROAD_MAIN]):
            return True
        ignore = None
        if self.fleet_at(A3, fleet=2) and A1.enemy_scale != 3 and (not self.fleet_at(A1, fleet=1)):
            ignore = SelectedGrids([A2])
        if self.fleet_at(G3, fleet=2):
            ignore = SelectedGrids([H3])
        self.clear_all_mystery(nearby=False, ignore=ignore)
        if self.clear_roadblocks([ROAD_MAIN], strongest=True):
            return True
        if self.clear_enemy(scale=(3,)):
            return True
        if self.clear_potential_roadblocks([ROAD_MAIN], strongest=True):
            return True
        if self.clear_enemy(strongest=True):
            return True
        return self.battle_default()
    def battle_5(self):
        ignore = None
        if self.fleet_at(A3, fleet=2):
            ignore = SelectedGrids([A2])
        if self.fleet_at(G3, fleet=2):
            ignore = SelectedGrids([H3])
        self.clear_all_mystery(nearby=False, ignore=ignore)
        if self.clear_roadblocks([ROAD_MAIN]):
            return True
        if self.fleet_at(A3, fleet=2) and A2.is_mystery:
            self.fleet_2.clear_chosen_mystery(A2)
        if self.fleet_at(G3, fleet=2) and H3.is_mystery:
            self.fleet_2.clear_chosen_mystery(H3)
        return self.fleet_boss.clear_boss()
