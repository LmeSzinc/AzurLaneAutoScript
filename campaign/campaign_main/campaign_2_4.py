class Campaign(CampaignBase):
    def battle_0(self):
        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_potential_roadblocks([road_main]):
            return True
        return self.battle_default()
    def battle_3(self):
        if not self.check_accessibility(G1, fleet='boss'):
            if self.clear_roadblocks([road_main]):
                return True
            return self.battle_default()
        return self.fleet_boss.clear_boss()
