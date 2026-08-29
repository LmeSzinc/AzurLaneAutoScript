class Campaign(CampaignBase):

    def map_data_init(self, map_):
        super().map_data_init(map_)
        C2.is_siren = True
        E2.is_siren = True
        G2.is_siren = True
