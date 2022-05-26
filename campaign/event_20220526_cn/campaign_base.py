from module.base.utils import color_similarity_2d
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.map_detection.grid import Grid
from module.template.assets import TEMPLATE_ENEMY_BOSS


class EventGrid(Grid):
    def predict_boss(self):
        # Small boss icon
        if self.relative_hsv_count(area=(0.03, -0.15, 0.63, 0.15), h=(358 - 3, 358 + 3), shape=(50, 20)) > 100:
            image = self.relative_crop((0.03, -0.15, 0.63, 0.15), shape=(50, 20))
            image = color_similarity_2d(image, color=(255, 77, 82))
            if TEMPLATE_ENEMY_BOSS.match(image, similarity=0.7):
                return True

        return False

    def predict_enemy_genre(self):
        image = self.relative_crop((-0.55, -0.2, 0.45, 0.2), shape=(50, 20))
        image = color_similarity_2d(image, color=(255, 150, 24))
        if TEMPLATE_ENEMY_BOSS.match(image, similarity=0.75):
            return 'Siren_Siren'

        return super().predict_enemy_genre()


class CampaignBase(CampaignBase_):
    grid_class = EventGrid
