from module.campaign.campaign_event import CampaignEvent
from module.event.assets import *
from module.exception import CampaignEnd
from module.logger import logger
from module.map.map_operation import MapOperation
from module.ocr.ocr import DigitCounter

OCR_REMAIN = DigitCounter(ESCORT_REMAIN, letter=(148, 255, 99), threshold=64)


class MaritimeEscort(MapOperation, CampaignEvent):
    def is_in_escort(self):
        return self.appear(ESCORT_CHECK, offset=(20, 20))

    def handle_in_stage(self):
        if self.is_in_escort():
            if self.in_stage_timer.reached():
                return True
            else:
                return False
        else:
            self.in_stage_timer.reset()
            return False

    def run_escort(self):
        """
        Just enter and retreat, get about 70% of maximum rewards.

        Pages:
            in: ESCORT_CHECK
            out: ESCORT_CHECK
        """
        logger.hr('Maritime escort', level=1)
        try:
            self.enter_map(ESCORT_HARD_ENTRANCE, mode='escort')
            self.withdraw()
        except CampaignEnd:
            pass

        logger.info('Maritime escort finished')

    def run(self):
        if self.event_time_limit_triggered():
            self.config.task_stop()

        self.ui_goto_main()
        self.ui_click(MAIN_GOTO_ESCORT, check_button=ESCORT_CHECK, offset=(20, 150), skip_first_screenshot=True)

        current, _, _ = OCR_REMAIN.ocr(self.device.image)
        if current > 0:
            self.run_escort()
        else:
            logger.info('Maritime escort already finished')

        self.config.task_delay(server_update=True)
