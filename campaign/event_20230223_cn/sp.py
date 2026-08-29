class Campaign(CampaignBase):

    def map_data_init(self, map_):
        super().map_data_init(map_)
        D4.is_siren = True
        D6.is_siren = True
        F4.is_siren = True
        F6.is_siren = True
