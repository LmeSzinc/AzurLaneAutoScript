class Campaign(CampaignBase):

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_any_enemy(sort=('cost_2',)):
            return True
        return self.battle_default()

    def battle_5(self):
        if self.clear_any_enemy(sort=('cost_2',)):
            return True
        return self.battle_default()
