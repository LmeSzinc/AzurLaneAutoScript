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
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    grid_class = GridCurrentFleet
    def in_sight(self, location, sight=None):
        location = location_ensure(location)
        node = location2node(location)
        if node == 'E3':
            return self.focus_to('E3')
        return super().in_sight(location, sight=sight)
    def battle_0(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=1):
            return True
        return self.battle_default()
    def battle_5(self):
        if self.clear_siren():
            return True
        if self.clear_filter_enemy(self.ENEMY_FILTER, preserve=0):
            return True
        return self.battle_default()
    def battle_6(self):
        return self.fleet_boss.clear_boss()
