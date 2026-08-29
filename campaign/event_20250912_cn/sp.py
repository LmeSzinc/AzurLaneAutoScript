class Campaign(CampaignBase):

    def map_data_init(self, map_):
        super().map_data_init(map_)
        B4.is_enemy = True
        B5.is_enemy = True
        C3.is_enemy = True
        C6.is_enemy = True
        G3.is_enemy = True
        G6.is_enemy = True
        H4.is_enemy = True
        H5.is_enemy = True
        D3.is_siren = True
        E4.is_siren = True
        F3.is_siren = True
