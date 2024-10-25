from module.base.utils import color_similarity_2d
from module.campaign.assets import SWITCH_20240725_COMBAT, SWITCH_20240725_STORY
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.campaign.campaign_ui import ModeSwitch
from module.map_detection.grid import Grid
from module.template.assets import TEMPLATE_ENEMY_BOSS

MODE_SWITCH_20240912 = ModeSwitch('Mode_switch_20240912', is_selector=True, offset=(30, 30))
MODE_SWITCH_20240912.add_status('combat', SWITCH_20240725_COMBAT, offset=(444, 4))
MODE_SWITCH_20240912.add_status('story', SWITCH_20240725_STORY, offset=(444, 4))


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
    def campaign_ensure_mode(self, mode='normal'):
        """
        Args:
            mode (str): 'normal', 'hard', 'ex', 'story'

        Returns:
            bool: If mode changed.
        """
        if mode == "story":
            MODE_SWITCH_20240912.set('story', main=self)
        elif mode in ['normal', 'hard', 'ex']:
            # First switch to combat mode and then select Hard or Normal.
            MODE_SWITCH_20240912.set('combat', main=self)
            # super().campaign_ensure_mode(mode)
