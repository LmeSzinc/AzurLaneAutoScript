class Campaign(CampaignBase):
    def battle_0(self):
        self.fleet_2_push_forward()
        return self.battle_clear_roadblocks(road_main, potential=True)
    def battle_6(self):
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                if self.clear_roadblocks([road_main]):
                    return True
        return self.fleet_boss.clear_boss()
