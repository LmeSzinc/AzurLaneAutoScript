class Campaign(CampaignBase):
    def battle_0(self):
        if self.fleet_at(D5, fleet=2):
            self.map.weight_data = '\n                10 10 30 10 10 20 30 40 10\n                10 10 10 10 10 30 10 50 10\n                30 10 10 10 10 10 10 60 10\n                10 10 10 10 10 10 10 70 10\n                10 30 10 10 10 10 10 10 10\n            '
        if self.fleet_at(F4, fleet=2):
            self.map.weight_data = '\n                10 10 30 10 10 10 10 10 10\n                10 10 20 30 10 30 10 10 10\n                30 10 20 10 10 10 10 10 10\n                10 10 10 10 10 10 10 10 10\n                10 30 10 10 10 10 10 10 10\n            '
        if self.fleet_at(F5, fleet=2):
            self.map.weight_data = '\n                10 10 30 10 10 10 10 10 10\n                10 10 20 30 10 30 10 10 10\n                30 10 20 10 10 10 10 10 10\n                10 10 10 10 10 10 10 10 10\n                10 30 10 10 10 10 10 10 10\n            '
        return self.battle_clear_roadblocks(road_main, potential=True)
    def battle_5(self):
        boss = self.map.select(is_boss=True)
        if boss:
            if not self.check_accessibility(boss[0], fleet='boss'):
                if self.clear_roadblocks([road_main]):
                    return True
        return self.fleet_boss.clear_boss()
