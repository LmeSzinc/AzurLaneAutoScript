class Campaign(CampaignBase):

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_enemy(sort=('weight', 'cost_2', 'cost_1')):
            return True
        return self.battle_default()

    def battle_5(self):
        if self.clear_siren():
            return True
        if self.clear_enemy(sort=('weight', 'cost_1')):
            return True
        return self.battle_default()
