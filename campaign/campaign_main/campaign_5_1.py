class Campaign(CampaignBase):

    def battle_4(self):
        self.clear_all_mystery()
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                return self.battle_default()
        return self.fleet_boss.clear_boss()
