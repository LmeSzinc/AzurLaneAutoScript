class Campaign(CampaignBase):
    MAP_AMBUSH_OVERLAY_TRANSPARENCY_THRESHOLD = 0.3
    MAP_AIR_RAID_OVERLAY_TRANSPARENCY_THRESHOLD = 0.25
    MAP_ENEMY_SEARCHING_OVERLAY_TRANSPARENCY_THRESHOLD = 0.65
    def battle_0(self):
        self.clear_all_mystery()
        return self.battle_default()
    def battle_3(self):
        self.clear_all_mystery()
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                return self.battle_default()
        return self.fleet_boss.clear_boss()
