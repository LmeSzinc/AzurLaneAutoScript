class Campaign(CampaignBase):

    def battle_5(self):
        if self.clear_siren():
            return True
        return self.fleet_boss.clear_boss()
