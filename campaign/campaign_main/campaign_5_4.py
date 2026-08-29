class Campaign(CampaignBase):
    def battle_0(self):
        if self.clear_roadblocks([road_center]):
            return True
        if self.clear_potential_roadblocks([road_ring]):
            return True
        return self.battle_default()
    def battle_4(self):
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                if self.clear_roadblocks([road_center]):
                    return True
                if self.clear_potential_roadblocks([road_ring]):
                    return True
        return self.fleet_boss.clear_boss()
