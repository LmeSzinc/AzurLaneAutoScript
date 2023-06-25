import re

from module.campaign.campaign_event import CampaignEvent
from module.coalition.assets import *
from module.coalition.combat import CoalitionCombat
from module.exception import ScriptError, ScriptEnd
from module.logger import logger
from module.ocr.ocr import Digit
from  module.log_res import LogRes

OCR_PT = Digit(FROSTFALL_OCR_PT, name='OCR_PT', letter=(198, 158, 82), threshold=128)


class Coalition(CoalitionCombat, CampaignEvent):
    run_count: int
    run_limit: int

    def get_event_pt(self):
        """
        Returns:
            int: PT amount, or 0 if unable to parse
        """
        pt = OCR_PT.ocr(self.device.image)
        LogRes(self.config).Pt = pt
        self.config.update()
        return pt

    def triggered_stop_condition(self):
        """
        Returns:
            bool: If triggered a stop condition.
        """
        # Run count limit
        if self.run_limit and self.config.StopCondition_RunCount <= 0:
            logger.hr('Triggered stop condition: Run count')
            self.config.StopCondition_RunCount = 0
            self.config.Scheduler_Enable = False
            return True
        # Oil limit
        if self.get_oil() < max(500, self.config.StopCondition_OilLimit):
            logger.hr('Triggered stop condition: Oil limit')
            self.config.task_delay(minute=(120, 240))
            return True
        # Event limit
        if self.event_pt_limit_triggered():
            logger.hr('Triggered stop condition: Event PT limit')
            return True
        # TaskBalancer
        if self.run_count >= 1:
            if self.config.TaskBalancer_Enable and self.triggered_task_balancer():
                logger.hr('Triggered stop condition: Coin limit')
                self.handle_task_balancer()
                return True

        return False

    def coalition_execute_once(self, event, stage, fleet):
        """
        Args:
            event:
            stage:
            fleet:

        Pages:
            in: in_coalition
            out: in_coalition
        """
        self.config.override(
            Campaign_Name=f'{event}_{stage}',
            Campaign_UseAutoSearch=False,
            Fleet_FleetOrder='fleet1_all_fleet2_standby',
        )
        if self.config.Coalition_Fleet == 'single' and self.config.Emotion_Fleet1Control == 'prevent_red_face':
            logger.warning('AL does not allow single coalition with emotion < 30, '
                           'emotion control is forced to prevent_yellow_face')
            self.config.override(Emotion_Fleet1Control='prevent_yellow_face')
        if stage == 'sp':
            # Multiple fleets are required in SP
            self.config.override(
                Coalition_Fleet='multi',
            )
        self.emotion.check_reduce(battle=self.coalition_get_battles(stage))

        self.enter_map(stage=stage, fleet=fleet)
        self.coalition_combat()

    @staticmethod
    def handle_stage_name(event, stage):
        stage = re.sub('[ \t\n]', '', str(stage)).lower()
        if event == 'coalition_20230323':
            stage = stage.replace('-', '')

        return event, stage

    def run(self, name='', stage='', fleet='', total=0):
        name = name if name else self.config.Campaign_Event
        stage = stage if stage else self.config.Campaign_Name
        fleet = fleet if fleet else self.config.Coalition_Fleet
        if not name or not stage or not fleet:
            raise ScriptError(f'RaidRun arguments unfilled. name={name}, stage={stage}, fleet={fleet}')

        name, stage = self.handle_stage_name(name, stage)
        self.run_count = 0
        self.run_limit = self.config.StopCondition_RunCount
        while 1:
            # End
            if total and self.run_count == total:
                break
            if self.event_time_limit_triggered():
                self.config.task_stop()

            # Log
            logger.hr(f'{name}_{stage}', level=2)
            if self.config.StopCondition_RunCount > 0:
                logger.info(f'Count remain: {self.config.StopCondition_RunCount}')
            else:
                logger.info(f'Count: {self.run_count}')

            # UI switches
            self.ui_goto_coalition()
            self.coalition_ensure_mode('battle')

            # End
            if self.triggered_stop_condition():
                break

            # Run
            try:
                self.coalition_execute_once(event=name, stage=stage, fleet=fleet)
            except ScriptEnd as e:
                logger.hr('Script end')
                logger.info(str(e))
                break

            # After run
            self.run_count += 1
            if self.config.StopCondition_RunCount:
                self.config.StopCondition_RunCount -= 1
            # End
            if self.triggered_stop_condition():
                break
            # Scheduler
            if self.config.task_switched():
                self.config.task_stop()
