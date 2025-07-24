from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.combat.assets import ALCHEMIST_MATERIAL_CONFIRM


class CampaignBase(CampaignBase_):
    def campaign_set_chapter_20241219(self, chapter, stage, mode='combat'):
        if self.config.MAP_CHAPTER_SWITCH_20241219:
            # TS is hard mode
            if chapter in ['ts']:
                self.ui_goto_event()
                self.campaign_ensure_mode_20241219('combat')
                self.campaign_ensure_aside_20241219('part2')
                self.campaign_ensure_chapter(chapter)
                return True
        return super().campaign_set_chapter_20241219(chapter, stage, mode)

    def handle_exp_info(self):
        # Extra confirm button in chapter TS
        if self.appear_then_click(ALCHEMIST_MATERIAL_CONFIRM, offset=(20, 20), interval=1):
            return False
        return super().handle_exp_info()
