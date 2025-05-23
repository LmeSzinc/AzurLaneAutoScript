from module.base.timer import Timer
from module.base.utils import area_in_area, area_pad
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.combat.assets import GET_ITEMS_1
from module.exception import CampaignNameError
from module.logger import logger
from module.ui.page import page_event


class CampaignBase(CampaignBase_):
    entrance_timer = Timer(2)

    def get_story_entrance(self):
        """
        Returns:
            Button: Or None if nothing matched.
        """
        # 5 story stage after clearing A2
        # You can't go anywhere unless you clicked it
        button = self.image_color_button(
            area=(66, 200, 1200, 690), color=(0, 0, 0),
            color_threshold=240, encourage=10, name='STORY_ENTRANCE')
        if button is None:
            return None
        # Blacklisted area
        if area_in_area(button.button, area_pad((424, 522, 444, 542), pad=-20)):
            return None
        return button

    def handle_story_entrance(self):
        if not self.entrance_timer.reached():
            return False

        entrance = self.get_story_entrance()
        if entrance is None:
            return False

        self.device.click(entrance)
        self.entrance_timer.reset()
        return True

    def ensure_no_stage_entrance(self, skip_first_screenshot=True):
        logger.info('ensure_no_stage_entrance')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.is_in_stage_page():
                # End
                try:
                    self._get_stage_name(self.device.image)
                    return True
                except (IndexError, CampaignNameError):
                    pass
                # Click
                if self.handle_story_entrance():
                    continue
            if self.handle_story_skip():
                self.interval_clear(GET_ITEMS_1)
                self.entrance_timer.clear()
                continue
            if self.appear_then_click(GET_ITEMS_1, offset=(20, 20), interval=3):
                self.entrance_timer.clear()
                continue

    def handle_in_stage(self):
        # Click after stage ended
        if self.is_in_stage_page():
            if self.handle_story_entrance():
                return False
        return super().handle_in_stage()

    def handle_get_chapter_additional(self):
        # Exit when having story entrance
        if self.get_story_entrance():
            raise CampaignNameError
        return super().handle_get_chapter_additional()

    def handle_campaign_ui_additional(self):
        if self.get_story_entrance():
            self.ensure_no_stage_entrance()
            return True
        return super().handle_campaign_ui_additional()

    def handle_exp_info(self):
        # Random background hits EXP_INFO_B
        if self.ui_page_appear(page_event):
            return False
        return super().handle_exp_info()
