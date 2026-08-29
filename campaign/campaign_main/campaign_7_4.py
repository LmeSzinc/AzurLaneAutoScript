class Campaign(CampaignBase):

    def battle_0(self):
        if self.fleet_2_step_on(fleet_2_step_on, roadblocks=[road_a5]):
            return True
        self.clear_all_mystery()
        if self.clear_roadblocks(roads):
            return True
        if self.clear_potential_roadblocks(roads):
            return True
        return self.battle_default()

    def battle_3(self):
        if self.fleet_2_step_on(fleet_2_step_on, roadblocks=[road_a5]):
            return True
        self.clear_all_mystery()
        if self.fleet_boss_index == 1:
            self.pick_up_ammo()
        if self.clear_roadblocks(roads):
            return True
        if self.clear_potential_roadblocks(roads):
            return True
        return self.battle_default()
