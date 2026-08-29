class Campaign(CampaignBase):
    def battle_0(self):
        if self.fleet_2_step_on(step_on, roadblocks=[road_middle]):
            return True
        self.clear_all_mystery()
        if self.clear_roadblocks([road_A6, road_H1, road_A1_left, road_A1_upper, road_H6_bottom, road_H6_right]):
            return True
        if self.clear_potential_roadblocks([road_A6, road_H1, road_A1_left, road_A1_upper, road_H6_bottom, road_H6_right]):
            return True
        if self.clear_roadblocks([road_MY]):
            return True
        if self.clear_first_roadblocks([road_A6, road_H1, road_A1_left, road_A1_upper, road_H6_bottom, road_H6_right]):
            return True
        return self.battle_default()
    def battle_4(self):
        return self.brute_clear_boss()
