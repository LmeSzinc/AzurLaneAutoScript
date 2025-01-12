from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.campaign.campaign_ui import MODE_SWITCH_20241219, ASIDE_SWITCH_20241219


class CampaignBase(CampaignBase_):
    STAGE_INCREASE = [
        'T1 > T2 > T3 > T4 > T5 > T6',
        'TTL1 > TTL2 > TTL3 > TTL4 > TTL5',
    ]

    @staticmethod
    def _campaign_get_chapter_index(name):
        """
        Args:
            name (str, int):

        Returns:
            int
        """
        if name == 'ttl':
            return 1
        return CampaignBase_._campaign_get_chapter_index(name)

    def campaign_set_chapter_20241219(self, chapter, stage, mode='combat'):
        if chapter == 't':
            self.ui_goto_event()
            MODE_SWITCH_20241219.set('combat', main=self)
            ASIDE_SWITCH_20241219.set('part1', main=self)
            self.campaign_ensure_chapter(chapter)
        if chapter == 'ttl':
            self.ui_goto_event()
            MODE_SWITCH_20241219.set('combat', main=self)
            ASIDE_SWITCH_20241219.set('part2', main=self)
            self.campaign_ensure_chapter(chapter)

        return super().campaign_set_chapter_20241219(chapter, stage, mode)
