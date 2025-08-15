from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.campaign.campaign_ui import ASIDE_SWITCH_20241219, MODE_SWITCH_20241219
from module.logger import logger


class CampaignBase(CampaignBase_):

    def campaign_set_chapter_20241219(self, chapter, stage, mode='combat'):
        if chapter in ['t', 'ht']:
            if self._campaign_name_is_hard(f'{chapter}{stage}'):
                self.config.override(Campaign_Mode='hard')
            self.ui_goto_event()
            MODE_SWITCH_20241219.set('combat', main=self)
            if stage in ['1', '2', '3']:
                ASIDE_SWITCH_20241219.set('part1', main=self)
            elif stage in ['4', '5', '6']:
                ASIDE_SWITCH_20241219.set('part2', main=self)
            else:
                logger.warning(f'Stage {chapter}{stage} is not in event')
            self.campaign_ensure_chapter(chapter)
            return True

        return super().campaign_set_chapter_20241219(chapter, stage, mode)
