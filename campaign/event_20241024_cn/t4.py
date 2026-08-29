class EventGrid(Grid):

    def predict_enemy_genre(self):
        if self.enemy_scale:
            return ''
        image = self.relative_crop((-0, -0.2, 0.8, 0.2), shape=(40, 20))
        image = color_similarity_2d(image, color=(255, 190, 84))
        if image[image > 221].shape[0] > 30:
            if TEMPLATE_ENEMY_BOSS.match(image, similarity=0.6, scaling=0.5):
                return 'Siren_Siren'
        return super().predict_enemy_genre()

class Campaign(CampaignBase):
    grid_class = EventGrid
