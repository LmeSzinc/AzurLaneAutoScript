class Campaign(CampaignBase):

    def battle_0(self):
        self.fleet_2_push_forward()
        if self.clear_siren(genre=('Siren_AzusaMiura', 'Siren_IoriMinase')):
            return True
        if self.clear_enemy(scale=(1,)):
            return True
        if self.clear_enemy(scale=(2,)):
            return True
        if self.clear_enemy(scale=(3,)):
            return True
        return self.battle_default()
