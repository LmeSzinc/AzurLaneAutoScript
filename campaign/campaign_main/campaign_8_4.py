class Campaign(CampaignBase):
    MAP_AMBUSH_OVERLAY_TRANSPARENCY_THRESHOLD = 0.45
    MAP_AIR_RAID_OVERLAY_TRANSPARENCY_THRESHOLD = 0.45
    def battle_0(self):
        self.fleet_2_push_forward()
        self.clear_all_mystery()
        if self.clear_roadblocks([road_D7, road_F3, road_main]):
            return True
        if self.clear_potential_roadblocks([road_D7, road_F3, road_main]):
            return True
        if self.clear_first_roadblocks([road_D7, road_F3, road_main]):
            return True
        return self.battle_default()
    def battle_4(self):
        self.clear_all_mystery()
        return self.brute_clear_boss()
