class Campaign(CampaignBase):
    MACHINE_FORTRESS = [I7]
    def battle_0(self):
        if self.clear_siren():
            return True
        return self.battle_default()
    def battle_5(self):
        return self.fleet_boss.clear_boss()
