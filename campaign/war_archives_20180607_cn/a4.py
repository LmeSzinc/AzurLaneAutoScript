class Campaign(CampaignBase):
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_potential_roadblocks([road_main]):
            return True
        return self.battle_default()
    def battle_4(self):
        return self.clear_boss()
