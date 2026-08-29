class Campaign(CampaignBase):
    MAP_AMBUSH_OVERLAY_TRANSPARENCY_THRESHOLD = 0.45
    MAP_AIR_RAID_OVERLAY_TRANSPARENCY_THRESHOLD = 0.45
    def battle_0(self):
        self.clear_all_mystery()
        self.fleet_2_push_forward()
        return self.battle_default()
    def battle_5(self):
        self.clear_all_mystery()
        return self.fleet_boss.brute_clear_boss()
    def handle_boss_appear_refocus(self, preset=(-3, -2)):
        return super().handle_boss_appear_refocus(preset)
