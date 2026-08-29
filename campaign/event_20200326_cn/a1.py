class Campaign(CampaignBase):

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_enemy(scale=(3,)):
            return True
        return self.battle_default()
