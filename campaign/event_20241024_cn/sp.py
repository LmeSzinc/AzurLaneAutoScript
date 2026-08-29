class Campaign(CampaignBase):

    def map_data_init(self, map_):
        super().map_data_init(map_)
        I2.is_siren = True
        J3.is_siren = True
        L3.is_siren = True
