class Campaign(CampaignBase):
    def battle_0(self):
        if self.battle_count >= 3:
            self.pick_up_ammo()
        if self.clear_roadblocks([road_main]):
            return True
        if self.clear_potential_roadblocks([road_main]):
            return True
        return self.battle_default()
    def battle_6(self):
        self.pick_up_ammo()
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                if self.clear_roadblocks([road_main]):
                    return True
        return self.fleet_boss.clear_boss()
