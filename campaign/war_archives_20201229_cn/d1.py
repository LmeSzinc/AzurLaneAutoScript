class Campaign(CampaignBase):

    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_enemy(scale=(1,)):
            return True
        if self.clear_enemy(scale=(2,), genre=['LightInvertedOrthant', 'MainInvertedOrthant']):
            return True
        if self.clear_enemy(scale=(3,), genre=['LightInvertedOrthant', 'MainInvertedOrthant']):
            return True
        if self.clear_enemy(scale=(2,), genre=['Enemy', 'CarrierInvertedOrthant']):
            return True
        if self.clear_enemy(scale=(3,), genre=['Enemy', 'CarrierInvertedOrthant']):
            return True
        return self.battle_default()
