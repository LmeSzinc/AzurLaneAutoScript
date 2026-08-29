class GridCurrentFleet(Grid):

    def predict_current_fleet(self):
        count = self.relative_hsv_count(area=(-0.5, -3.5, 0.5, -2.5), h=(141 - 3, 141 + 10), shape=(50, 50))
        if count < 150:
            return False
        image = self.relative_crop((-0.5, -3.5, 0.5, -2.5), shape=(60, 60))
        image = color_similarity_2d(image, color=(24, 255, 107))
        if not TEMPLATE_FLEET_CURRENT.match(image):
            return False
        return True

class Campaign(CampaignBase):
    grid_class = GridCurrentFleet

    def in_sight(self, location, sight=None):
        location = location_ensure(location)
        node = location2node(location)
        if node == 'E3':
            return self.focus_to('E3')
        return super().in_sight(location, sight=sight)
