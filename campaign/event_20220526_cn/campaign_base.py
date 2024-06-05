from module.base.utils import color_similarity_2d
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.map_detection.grid import Grid
from module.template.assets import TEMPLATE_ENEMY_BOSS


class EventGrid(Grid):
    def predict_enemy_genre(self):
        image = self.relative_crop((-0.55, -0.2, 0.45, 0.2), shape=(50, 20))
        image = color_similarity_2d(image, color=(255, 150, 24))
        if image[image > 221].shape[0] > 200:
            if TEMPLATE_ENEMY_BOSS.match(image, similarity=0.6):
                return 'Siren_Siren'

        return super().predict_enemy_genre()

    def predict_boss(self):
        if self.enemy_genre == 'Siren_Siren':
            return False
        return super().predict_boss()


class CampaignBase(CampaignBase_):
    pass
