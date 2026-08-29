class Campaign(CampaignBase):
    def battle_0(self):
        if self.fleet_2_step_on(step_on, roadblocks=[road_in_map]):
            return True
        if self.clear_roadblocks([road_boss]):
            return True
        if self.clear_roadblocks([road_mystery]):
            return True
        self.clear_all_mystery()
        if self.clear_potential_roadblocks([road_boss]):
            return True
        if self.clear_potential_roadblocks([road_mystery]):
            return True
        return self.battle_default()
    def battle_4(self):
        self.clear_all_mystery()
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                return self.clear_roadblocks([road_boss])
        return self.fleet_boss.clear_boss()
