class Campaign(CampaignBase):
    def battle_0(self):
        if not self.config.MAP_HAS_MOVABLE_ENEMY:
            self.fleet_2_push_forward()
        if self.clear_siren():
            return True
        self.clear_mechanism()
        if self.config.MAP_HAS_MOVABLE_ENEMY:
            self.fleet_2_push_forward()
        if self.clear_roadblocks([road_main]):
            return True
        return self.battle_default()
    def battle_5(self):
        return self.fleet_boss.clear_boss()
