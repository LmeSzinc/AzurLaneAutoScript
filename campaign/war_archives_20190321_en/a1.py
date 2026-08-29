class EventGrid(Grid):

    def predict_current_fleet(self):
        count = self.relative_hsv_count(area=(-0.5, -3.5, 0.5, -2.5), h=(141 - 3, 141 + 10), shape=(50, 50))
        if count < 200:
            return False
        return True

class Campaign(CampaignBase):
    grid_class = EventGrid
    ENEMY_FILTER = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'
    def battle_0(self):
        if self.fleet_2_push_forward():
            return True
        return self.battle_default()
    def battle_5(self):
        return self.fleet_boss.clear_boss()
