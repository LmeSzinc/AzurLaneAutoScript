from module.base.utils import color_similarity_2d
from module.map_detection.grid import Grid
from module.template.assets import TEMPLATE_ENEMY_BOSS


class CurrentFleetGrid(Grid):
    def predict_current_fleet(self):
        count = self.relative_hsv_count(area=(-0.5, -3.5, 0.5, -2.5), h=(141 - 3, 141 + 10), shape=(50, 50))
        if count < 600:
            return False
        # No template matching
        return True


class SirenIconGrid(Grid):
    # Event grids with sirens having small boss icons
    def predict_enemy_genre(self):
        if self.enemy_scale:
            return ''

        image = self.relative_crop((-0, -0.2, 0.8, 0.2), shape=(40, 20))
        image = color_similarity_2d(image, color=(255, 150, 24))
        if image[image > 221].shape[0] > 30:
            if TEMPLATE_ENEMY_BOSS.match(image, similarity=0.6, scaling=0.5):
                return 'Siren_Siren'

        return super().predict_enemy_genre()

    def predict_boss(self):
        if self.enemy_genre == 'Siren_Siren':
            return False
        return super().predict_boss()
