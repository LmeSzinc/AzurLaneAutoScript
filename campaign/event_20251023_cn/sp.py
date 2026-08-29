class Campaign(CampaignBase):

    def map_data_init(self, map_):
        super().map_data_init(map_)
        F4.is_siren = True
        F6.is_siren = True
        G5.is_siren = True
