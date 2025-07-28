from module.campaign.assets import EVENT_20221124_CHECK
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.combat.assets import ALCHEMIST_MATERIAL_CONFIRM
from module.handler.fast_forward import AUTO_SEARCH
from module.logger import logger
from module.template.assets import TEMPLATE_STAGE_HALF_PERCENT, TEMPLATE_STAGE_CLEAR_20240725
from module.ui.page import page_campaign_menu, page_event
from module.war_archives.assets import WAR_ARCHIVES_CAMPAIGN_CHECK


class CampaignBaseT(CampaignBase_):
    def ui_goto_event_20250724(self):
        # Already in page_event, skip event_check.
        if self.ui_get_current_page() == page_event:
            if self.appear(WAR_ARCHIVES_CAMPAIGN_CHECK, offset=(20, 20)):
                logger.info('At war archives')
                self.ui_goto_main()
            elif self.appear(EVENT_20221124_CHECK, offset=(20, 20)):
                logger.info('At event 20221124')
                self.ui_goto_main()
            else:
                logger.info('Already at page_event')
                return True
        return True

    def campaign_set_chapter_20241219(self, chapter, stage, mode='combat'):
        self.ui_goto_event_20250724()
        return super().campaign_set_chapter_20241219(chapter, stage, mode)

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
            self.ui_goto_event_20250724()
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
