from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger


class CampaignBase(CampaignBase_):
    def campaign_set_chapter_20241219(self, chapter, stage, mode='combat'):
        if self.config.MAP_CHAPTER_SWITCH_20241219:
            if self._campaign_name_is_hard(f'{chapter}{stage}'):
                self.config.override(Campaign_Mode='hard')

            if chapter in ['t', 'ht']:
                self.ui_goto_event()
                self.campaign_ensure_mode_20241219('combat')
                if stage in ['1', '2', '3']:
                    self.campaign_ensure_aside_20241219('part1')
                elif stage in ['4', '5', '6']:
                    self.campaign_ensure_aside_20241219('part2')
                else:
                    logger.warning(f'Stage {chapter}{stage} is not in event_20250814')
                self.campaign_ensure_chapter(chapter)
                return True
        return super().campaign_set_chapter_20241219(chapter, stage, mode)
