class Campaign(CampaignBase):
    grid_class = GridCurrentFleet

    def in_sight(self, location, sight=None):
        location = location_ensure(location)
        node = location2node(location)
        if node == 'E3':
            return self.focus_to('E3')
        return super().in_sight(location, sight=sight)
