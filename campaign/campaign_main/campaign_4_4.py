class Campaign(CampaignBase):
    MAP_AMBUSH_OVERLAY_TRANSPARENCY_THRESHOLD = 0.3
    MAP_AIR_RAID_OVERLAY_TRANSPARENCY_THRESHOLD = 0.25
    MAP_ENEMY_SEARCHING_OVERLAY_TRANSPARENCY_THRESHOLD = 0.65
    def battle_0(self):
        return self.battle_clear_roadblocks(road_main, potential=True)
    def battle_4(self):
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                if self.clear_roadblocks([road_main]):
                    return True
                if self.clear_potential_roadblocks([road_main]):
                    return True
        return self.fleet_boss.clear_boss()
