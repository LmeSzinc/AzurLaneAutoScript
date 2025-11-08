from module.campaign.assets import EVENT_20250724_PT_ICON
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.combat.assets import ALCHEMIST_MATERIAL_CONFIRM
from module.handler.fast_forward import AUTO_SEARCH
from module.logger import logger
from module.template.assets import TEMPLATE_STAGE_CLEAR_20240725, TEMPLATE_STAGE_HALF_PERCENT
from module.ui.page import page_campaign_menu, page_event


class CampaignBaseT(CampaignBase_):
    def ui_goto_event(self):
        if self.appear(EVENT_20250724_PT_ICON, offset=(20, 20)) and self.ui_page_appear(page_event):
            logger.info('Already at EVENT_20250724')
            return True
        self.ui_ensure(page_campaign_menu)
        # Check event availability
        if self.is_event_entrance_available():
            self.ui_goto(page_event)
            return True
    
    def campaign_extract_name_image(self, image):
        if self.config.SERVER == 'en':
            # EN has small stage name
            digits = []
            if 'half' in self.config.STAGE_ENTRANCE:
                digits += self.campaign_match_multi(
                    TEMPLATE_STAGE_HALF_PERCENT,
                    image, self._stage_image_gray,
                    name_offset=(54, 3), name_size=(60, 10)
                )
            if '20240725' in self.config.STAGE_ENTRANCE:
                digits += self.campaign_match_multi(
                    TEMPLATE_STAGE_CLEAR_20240725,
                    image, self._stage_image_gray,
                    name_offset=(73, 2), name_size=(60, 10)
                )
            return digits

        return super().campaign_extract_name_image(image)


class CampaignBaseTS(CampaignBaseT):
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
