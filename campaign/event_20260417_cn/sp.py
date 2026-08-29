class Campaign(CampaignBase):

    def _expected_end(self, expected):
        if self.battle_count == 3:
            return self.event_animation_end
        return super()._expected_end(expected)
