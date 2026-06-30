from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger


class CampaignBase(CampaignBase_):
    def campaign_set_chapter_20241219(self, chapter, stage, mode='combat'):
        if self.config.MAP_CHAPTER_SWITCH_20241219:
            if chapter in ['t']:
                self.ui_goto_sp()
                self.campaign_ensure_mode_20241219('combat')
                if stage in ['1', '2', '3']:
                    self.campaign_ensure_aside_20241219('part1')
                elif stage in ['4', '5', '6']:
                    self.campaign_ensure_aside_20241219('part2')
                else:
                    logger.warning(f'Stage {chapter}{stage} is not in event_20241024')
                self.campaign_ensure_chapter(chapter)
                return True
            if chapter in ['ex_sp']:
                self.ui_goto_sp()
                self.campaign_ensure_mode_20241219('combat')
                self.campaign_ensure_aside_20241219('sp')
                self.campaign_ensure_chapter(chapter)
                return True
        return super().campaign_set_chapter_20241219(chapter, stage, mode)
