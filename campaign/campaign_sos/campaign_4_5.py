class Campaign(CampaignBase):
    MAP_AMBUSH_OVERLAY_TRANSPARENCY_THRESHOLD = 0.3
    MAP_AIR_RAID_OVERLAY_TRANSPARENCY_THRESHOLD = 0.25
    MAP_ENEMY_SEARCHING_OVERLAY_TRANSPARENCY_THRESHOLD = 0.65
    def battle_0(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True
        return self.battle_default()
    def battle_3(self):
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
    def battle_4(self):
        return self.fleet_boss.clear_boss()
