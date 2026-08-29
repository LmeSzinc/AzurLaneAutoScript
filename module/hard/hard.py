from campaign.campaign_hard.campaign_hard import Campaign
from module.campaign.map_loader import load_map
from module.campaign.run import CampaignRun
from module.handler.fast_forward import to_map_file_name
from module.hard.assets import *  # noqa: F403  (data-bundle star import)
from module.logger import logger
from module.ocr.ocr import Digit

OCR_HARD_REMAIN = Digit(OCR_HARD_REMAIN, letter=(123, 227, 66), threshold=128, alphabet="0123")


class CampaignHard(CampaignRun):
    equipment_has_take_on = False
    campaign: Campaign

    def run(self):
        logger.hr("Campaign hard", level=1)
        name = to_map_file_name(self.config.Hard_HardStage)
        self.config.override(
            Campaign_Mode="hard",
            Campaign_UseFleetLock=True,
            Campaign_UseAutoSearch=True,
            Fleet_FleetOrder="fleet1_all_fleet2_standby"
            if self.config.Hard_HardFleet == 1
            else "fleet1_standby_fleet2_all",
            Emotion_Mode="nothing",  # Dont calculate and dont ignore
        )
        # Equipment take on
        # campaign/campaign_hard/campaign_hard.py Campaign.fleet_preparation()

        # Initial
        # Logic module: Config/Campaign only (no MAP of its own).
        self.load_campaign_logic(name="campaign_hard", folder="campaign_hard")
        # Map module: the stage map comes from campaign_main (normal mode).
        self.campaign.MAP = load_map('campaign_main', name).MAP

        # UI ensure
        self.device.screenshot()
        self.campaign.device.image = self.device.image
        self.campaign.ensure_campaign_ui(name=self.config.Hard_HardStage, mode="hard")

        # Run
        remain = OCR_HARD_REMAIN.ocr(self.device.image)
        logger.attr("Remain", remain)
        for _n in range(remain):
            self.campaign.run()

        self.campaign.ensure_auto_search_exit()
        # self.campaign.equipment_take_off_when_finished()

        # Scheduler
        self.config.task_delay(server_update=True)
        self.config.task_call("Reward")
