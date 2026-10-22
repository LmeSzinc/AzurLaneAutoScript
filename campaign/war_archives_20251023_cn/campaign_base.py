from module.campaign.campaign_ui import ASIDE_SWITCH_20241219
from ..campaign_war_archives.campaign_base import CampaignBase as CampaignBase_


class CampaignBase(CampaignBase_):
    STAGE_INCREASE = [
        """
        T1 > T2 > T3 > T4 > T5 > T6
        """
    ]

    def campaign_set_chapter_20241219(self, chapter, stage, mode='combat'):
        if chapter == 't' and stage in ['1', '2', '3', '4', '5', '6']:
            self.ui_goto_sp()
            if stage in ['1', '2', '3']:
                ASIDE_SWITCH_20241219.set('part2', main=self)
            else:
                ASIDE_SWITCH_20241219.set('sp', main=self)
            self.campaign_ensure_chapter(chapter)
            return True

        return super().campaign_set_chapter_20241219(chapter, stage, mode)
