class Campaign(CampaignBase):

    def battle_0(self):
        if self.fleet_2_step_on(step_on, roadblocks=[road_middle]):
            return True
        self.clear_all_mystery()
        if self.clear_roadblocks([road_A1, road_H1]):
            return True
        if self.mystery_count < 1 and self.clear_roadblocks([road_MY]):
            return True
        if self.clear_potential_roadblocks([road_A1, road_H1]):
            return True
        if self.clear_first_roadblocks([road_A1, road_H1]):
            return True
        return self.battle_default()
