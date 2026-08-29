class Campaign(CampaignBase):

    def battle_5(self):
        if self.config.FLEET_BOSS == 1:
            self.pick_up_ammo()
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                if self.clear_roadblocks([road_main]):
                    return True
        return self.fleet_boss.clear_boss()
