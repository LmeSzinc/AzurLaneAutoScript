class Campaign(CampaignBase):

    def map_data_init(self, map_):
        super().map_data_init(map_)
        C1.is_siren = True
        D2.is_siren = True
        E1.is_siren = True
