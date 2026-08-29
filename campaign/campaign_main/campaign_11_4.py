class Campaign(CampaignBase):
    def battle_0(self):
        if self.fleet_2_step_on(step_on, roadblocks=[road_boss]):
            return True
        return self.battle_clear_roadblocks(road_boss, potential=True)
    def battle_6(self):
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                return self.clear_roadblocks([road_boss])
        return self.fleet_boss.clear_boss()
