class Campaign(CampaignBase):

    def get_map_clear_percentage(self):
        """
            map clear here is shorter than normal, about 70% at max

            Returns:
                float: 0 to 1.
            """
        return super().get_map_clear_percentage() * 1.4

    def battle_0(self):
        if not self.map_is_clear_mode:
            for grid in self.map:
                grid.may_siren = True
            self.fleet_2_push_forward()
        if self.clear_siren():
            return True
        return self.battle_default()
