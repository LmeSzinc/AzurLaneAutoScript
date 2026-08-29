class Campaign(CampaignBase):
    def battle_0(self):
        if self.fleet_2_step_on(fleet_2_step_on, roadblocks=roads):
            return True
        self.clear_all_mystery()
        if self.clear_roadblocks(roads):
            return True
        if self.clear_potential_roadblocks(roads):
            return True
        return self.battle_default()
    def battle_5(self):
        self.clear_all_mystery()
        boss = self.map.select(is_boss=True)
        if boss:
            boss = boss[0]
            if boss == A1:
                road_boss = [road_a1]
            elif boss == C6:
                road_boss = [road_c6]
            elif boss == H1:
                road_boss = [road_h1]
            elif boss == H5:
                road_boss = [road_h5]
            else:
                logger.warning(f'Unexpected boss grid: {boss}')
                road_boss = roads
            if not self.check_accessibility(boss, fleet='boss'):
                return self.clear_roadblocks(road_boss)
        return self.fleet_boss.clear_boss()
