from module.base.timer import Timer
from module.base.utils import crop, rgb2gray
from module.campaign.assets import (
    EVENT_20230817_STORY,
    TEMPLATE_EVENT_20230817_STORY_E1,
    TEMPLATE_EVENT_20230817_STORY_E2
)
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger
from module.ui.page import page_event


class CampaignBase(CampaignBase_):
    def handle_chapter_additional(self):
        """
        event_20230817_cn has stories act as stage entrance,
        stories must be cleared to unlock stages.
        """
        if self.get_story_button():
            self.event_20230817_story()
            return True
        else:
            logger.info('No event_20230817_story')
            return False

    def get_story_button(self):
        """
        This method costs about 26ms.

        Returns:
            Button:
        """
        # Story before A1, E0-1 ~ E0-3
        if self.appear(EVENT_20230817_STORY, offset=(20, 20)):
            return EVENT_20230817_STORY

        # Smaller image to run faster
        area = (73, 135, 1223, 583)
        image = rgb2gray(crop(self.device.image, area=area))

        # E1-1 ~ E1-2
        sim, button = TEMPLATE_EVENT_20230817_STORY_E1.match_result(image)
        if sim > 0.85:
            button = button.move(area[:2])
            return button

        # E21-1 ~ E2-7
        sim, button = TEMPLATE_EVENT_20230817_STORY_E2.match_result(image)
        if sim > 0.85:
            button = button.move(area[:2])
            return button

        return None

    def event_20230817_story(self, skip_first_screenshot=True):
        logger.hr('event_20230817_story', level=2)
        confirm = Timer(1, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.ui_page_appear(page_event):
                if confirm.reached():
                    break
            else:
                confirm.reset()

            if self.handle_story_skip():
                continue

            button = self.get_story_button()
            if button:
                self.device.click(button)

    def is_stage_page_has_entrance(self):
        if self.get_story_button():
            return True
        return super().is_stage_page_has_entrance()
