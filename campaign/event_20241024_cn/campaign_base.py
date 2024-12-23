from module.base.utils import color_similarity_2d
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.campaign.campaign_ui import ASIDE_SWITCH_20241219, MODE_SWITCH_20241219
from module.logger import logger
from module.map_detection.grid import Grid
from module.template.assets import TEMPLATE_ENEMY_BOSS


class EventGrid(Grid):
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


class CampaignBase(CampaignBase_):
    STAGE_INCREASE = [
        """
        T1 > T2 > T3 > T4 > T5 > T6
        """
    ]

    def campaign_set_chapter_20241219(self, chapter, stage, mode='combat'):
        if chapter == 't':
            self.ui_goto_event()
            MODE_SWITCH_20241219.set('combat', main=self)
            if stage in ['1', '2', '3']:
                ASIDE_SWITCH_20241219.set('part1', main=self)
            elif stage in ['4', '5', '6']:
                ASIDE_SWITCH_20241219.set('part2', main=self)
            else:
                logger.warning(f'Stage {chapter}{stage} is not in event_20241024')
            self.campaign_ensure_chapter(index=chapter)

        return super().campaign_set_chapter_20241219(chapter, stage, mode)
