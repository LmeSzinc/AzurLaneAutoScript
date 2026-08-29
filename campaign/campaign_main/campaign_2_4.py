class Campaign(CampaignBase):

    def battle_3(self):
        if not self.check_accessibility(G1, fleet='boss'):
            if self.clear_roadblocks([road_main]):
                return True
            return self.battle_default()
        return self.fleet_boss.clear_boss()
