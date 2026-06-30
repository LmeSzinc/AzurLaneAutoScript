from module.base.button import Button
from module.campaign.assets import EVENT_20260417_PT_ICON, EVENT_20260417_DETAIL, EVENT_20260417_DETAIL_CHECK, EVENT_20260417_DETAIL_WHITE, EVENT_20260417_ENTRANCE
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger
from module.ui.page import page_campaign_menu, page_event, page_main_white

EVENT_ANIMATION = Button(area=(49, 229, 119, 400), color=(118, 215, 240), button=(49, 229, 119, 400),
                         name='EVENT_ANIMATION')


class CampaignBase(CampaignBase_):
    def ui_goto_event(self):
        if self.appear(EVENT_20260417_PT_ICON, offset=(40, 20)) and self.ui_page_appear(page_event):
            logger.info('Already at EVENT_20260417')
            return True
        self.ui_ensure(page_campaign_menu)
        if self.is_event_entrance_available():
            if self.config.SERVER == 'tw':
                self.ui_goto(page_event)
            else:
                self.ui_goto_main()
                if self.ui_page_appear(page_main_white):
                    self.ui_click(EVENT_20260417_DETAIL_WHITE, check_button=EVENT_20260417_DETAIL_CHECK)
                else:
                    self.ui_click(EVENT_20260417_DETAIL, check_button=EVENT_20260417_DETAIL_CHECK)
                self.ui_click(EVENT_20260417_ENTRANCE, check_button=EVENT_20260417_PT_ICON,
                              appear_button=EVENT_20260417_DETAIL_CHECK, offset=(40, 20))
                return True

    @staticmethod
    def _campaign_ocr_result_process(result):
        result = CampaignBase_._campaign_ocr_result_process(result)
        if result in ['ysp', 'usp', 'vsp']:
            result = 'sp'
        return result

    def is_event_animation(self):
        """
        Animation in events after cleared an enemy.

        Returns:
            bool: If animation appearing.
        """
        appear = self.appear(EVENT_ANIMATION)
        if appear:
            logger.info('DOA animation, waiting')
        return appear

    def event_animation_end(self):
        if not self.appear(EVENT_ANIMATION):
            return False
        # wait until EVENT_ANIMATION closed
        for _ in self.loop():
            if self.is_event_animation():
                continue
            break
        # now in_map
        return True
