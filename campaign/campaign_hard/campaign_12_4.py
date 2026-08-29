class Campaign(CampaignBase):
    def battle_0(self):
        if self.battle_count >= 3:
            self.pick_up_ammo()
        return self.battle_clear_roadblocks(road_main, potential=True)
    def battle_7(self):
        self.pick_up_ammo()
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                if self.clear_roadblocks([road_main]):
                    return True
        return self.fleet_boss.clear_boss()
