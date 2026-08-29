class Campaign(CampaignBase):

    def map_data_init(self, map_):
        super().map_data_init(map_)
        D5.is_siren = True
        E4.is_siren = True
        E6.is_siren = True
