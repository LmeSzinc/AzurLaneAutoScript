from module.base.utils import color_similarity_2d
from module.campaign.assets import *
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.campaign.campaign_ui import ModeSwitch
from module.logger import logger
from module.map_detection.grid import Grid
from module.template.assets import TEMPLATE_ENEMY_BOSS

MODE_SWITCH_20240725 = ModeSwitch('Mode_switch_20240725', is_selector=True, offset=(30, 30))
MODE_SWITCH_20240725.add_state('combat', SWITCH_20240725_COMBAT, offset=(444, 4))
MODE_SWITCH_20240725.add_state('story', SWITCH_20240725_STORY, offset=(444, 4))

CHAPTER_SWITCH_20241024 = ModeSwitch('Chapter_switch_20241024', is_selector=True, offset=(30, 30))
CHAPTER_SWITCH_20241024.add_state('ab', CHAPTER_20241024_AB)
CHAPTER_SWITCH_20241024.add_state('cd', CHAPTER_20241024_CD)
CHAPTER_SWITCH_20241024.add_state('sp', CHAPTER_20241024_SP)
CHAPTER_SWITCH_20241024.add_state('ex', CHAPTER_20241024_EX)


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

    def campaign_set_chapter(self, name, mode='normal'):
        """
        Args:
            name (str): Campaign name, such as '7-2', 'd3', 'sp3'.
            mode (str): 'normal' or 'hard'.
        """
        chapter, stage = self._campaign_separate_name(name)

        if chapter in ['t']:
            self.ui_goto_event()
            MODE_SWITCH_20240725.set('combat', main=self)
            if stage in ['1', '2', '3']:
                CHAPTER_SWITCH_20241024.set('ab', main=self)
            elif stage in ['4', '5', '6']:
                CHAPTER_SWITCH_20241024.set('cd', main=self)
            else:
                logger.warning(f'Stage {name} is not in CHAPTER_SWITCH_20241024')
            self.campaign_ensure_chapter(index=chapter)
        elif chapter in ['ex_sp']:
            self.ui_goto_event()
            MODE_SWITCH_20240725.set('combat', main=self)
            CHAPTER_SWITCH_20241024.set('sp', main=self)
            self.campaign_ensure_chapter(index=chapter)
        elif chapter in ['ex_ex']:
            self.ui_goto_event()
            MODE_SWITCH_20240725.set('combat', main=self)
            CHAPTER_SWITCH_20241024.set('ex', main=self)
            self.campaign_ensure_chapter(index=chapter)
        else:
            logger.warning(f'Unknown campaign chapter: {name}')
