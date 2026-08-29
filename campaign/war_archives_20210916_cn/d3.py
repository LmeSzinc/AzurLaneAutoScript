class Campaign(CampaignBase):

    def battle_6(self):
        if self.clear_siren():
            return True
        return self.fleet_boss.clear_boss()
