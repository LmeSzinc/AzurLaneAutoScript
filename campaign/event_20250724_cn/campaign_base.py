from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.combat.assets import ALCHEMIST_MATERIAL_CONFIRM
from module.handler.fast_forward import AUTO_SEARCH


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

    def get_map_clear_percentage(self):
        if AUTO_SEARCH.appear(main=self):
            return 1.00
        return super().get_map_clear_percentage()

    def map_get_info(self):
        super().map_get_info()

        # Chapter TS don't have clear percentage
        # if auto search appears, consider it cleared
        appear = AUTO_SEARCH.appear(main=self)
        self.map_is_100_percent_clear = self.map_is_3_stars = self.map_is_threat_safe = appear
        self.map_has_clear_mode = appear
        self.map_show_info()
