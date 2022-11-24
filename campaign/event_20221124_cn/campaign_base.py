from module.campaign.assets import SWITCH_1_HARD_ALCHEMIST
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.campaign.campaign_ui import MODE_SWITCH_1

for state in MODE_SWITCH_1.status_list:
    if state['status'] == 'hard':
        state['check_button'] = SWITCH_1_HARD_ALCHEMIST
        state['click_button'] = SWITCH_1_HARD_ALCHEMIST


class CampaignBase(CampaignBase_):
    STAGE_INCREASE = [
        'T1 > T2 > T3 > TS1 > T4 > T5',
        'HT1 > HT2 > HT3 > HT4 > HT5',
    ]

    def campaign_set_chapter_event(self, chapter, mode='normal'):
        if chapter == 'ts':
            self.ui_goto_event()
            self.campaign_ensure_mode('normal')
            return True

        return super().campaign_set_chapter_event(chapter, mode=mode)

    @staticmethod
    def _campaign_separate_name(name):
        if name == 'ts1':
            return 't', '1'

        return CampaignBase_._campaign_separate_name(name)
