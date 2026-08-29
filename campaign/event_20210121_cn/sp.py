class Campaign(CampaignBase):

    def battle_0(self):
        if self.map.select(is_siren=True):
            if self.fleet_2_protect():
                return True
        else:
            self.fleet_2_push_forward()
        if self.clear_siren():
            return True
        return self.battle_default()
