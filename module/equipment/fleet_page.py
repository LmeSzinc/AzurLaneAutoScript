from abc import abstractmethod, ABC

from module.base.timer import Timer
from module.campaign.campaign_base import CampaignBase
from module.campaign.run import CampaignRun
from module.equipment.assets import *
from module.map.assets import MAP_PREPARATION, FLEET_PREPARATION
from module.ocr.ocr import Digit
from module.ui.page import page_fleet
from module.ui.ui import UI

FLEET_INDEX = Digit(OCR_FLEET_INDEX, letter=(90, 154, 255), threshold=128, alphabet='123456')


class FleetPage(ABC):
    def __init__(self, main):
        self.main = main

    @abstractmethod
    def ensure_fleet_page(self):
        pass


class NormalFleetPage(FleetPage):
    def __init__(self, main: UI, fleet_index: int):
        super().__init__(main)
        self.fleet_index = fleet_index

    def ensure_fleet_page(self):
        self.main.ui_ensure(page_fleet)
        self.main.ui_ensure_index(self.fleet_index, letter=FLEET_INDEX,
                                  next_button=FLEET_NEXT, prev_button=FLEET_PREV,
                                  skip_first_screenshot=True)


class HardFleetPage(FleetPage):
    def __init__(self, main: CampaignRun, campaign: CampaignBase):
        super().__init__(main=main)
        self.campaign = campaign

    def ensure_fleet_page(self):
        self.campaign.ensure_campaign_ui(self.main.stage, self.main.config.Campaign_Mode)
        self.campaign.ENTRANCE.area = self.campaign.ENTRANCE.button
        campaign_timer = Timer(5)
        map_timer = Timer(5)
        campaign_click = 0
        map_click = 0
        for _ in self.main.loop():
            if self.main.appear(FLEET_PREPARATION, offset=(20, 50)):
                break
            if map_timer.reached() \
                    and self.campaign.handle_map_mode_switch(self.main.config.Campaign_Mode) \
                    and self.campaign.handle_map_preparation():
                self.main.device.click(MAP_PREPARATION)
                map_click += 1
                map_timer.reset()
                campaign_timer.reset()
            if campaign_timer.reached() and self.main.appear_then_click(self.campaign.ENTRANCE):
                campaign_click += 1
                campaign_timer.reset()
                continue
