from module.base.timer import Timer
from module.campaign.assets import EVENT_20230817_STORY
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger
from module.ui.page import page_event


class CampaignBase(CampaignBase_):
    def handle_chapter_additional(self):
        if self.appear(EVENT_20230817_STORY, offset=(20, 20)):
            self.event_20230817_story()
            return True
        else:
            return False

    def event_20230817_story(self, skip_first_screenshot=True):
        logger.hr('event_20230817_story', level=2)
        confirm = Timer(1, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.ui_page_appear(page_event):
                if confirm.reached():
                    break
            else:
                confirm.reset()

            if self.appear_then_click(EVENT_20230817_STORY, offset=(20, 20), interval=1):
                continue
            if self.handle_story_skip():
                continue
