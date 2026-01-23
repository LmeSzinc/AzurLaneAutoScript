import re

from module.campaign.campaign_event import CampaignEvent
from module.coalition.assets import *
from module.coalition.combat import CoalitionCombat
from module.exception import ScriptEnd, ScriptError
from module.logger import logger
from module.ocr.ocr import Digit
from module.ui.page import page_campaign_menu


class AcademyPtOcr(Digit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alphabet += ':'

    def after_process(self, result):
        logger.attr(self.name, result)
        try:
            # 累计: 840
            result = result.rsplit(':')[1]
        except IndexError:
            pass
        return super().after_process(result)


class DALPtOcr(Digit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alphabet += 'X'

    def after_process(self, result):
        logger.attr(self.name, result)
        try:
            # X9100
            result = result.rsplit('X')[1]
        except IndexError:
            pass
        return super().after_process(result)


class Coalition(CoalitionCombat, CampaignEvent):
    run_count: int
    run_limit: int

    def get_event_pt(self):
        """
        Returns:
            int: PT amount, or 0 if unable to parse
        """
        event = self.config.Campaign_Event
        if event == 'coalition_20230323':
            ocr = Digit(FROSTFALL_OCR_PT, name='OCR_PT', letter=(198, 158, 82), threshold=128)
        elif event == 'coalition_20240627':
            ocr = AcademyPtOcr(ACADEMY_PT_OCR, name='OCR_PT', letter=(255, 255, 255), threshold=128)
        elif event == 'coalition_20250626':
            # use generic ocr model
            ocr = Digit(NEONCITY_PT_OCR, name='OCR_PT', lang='cnocr', letter=(208, 208, 208), threshold=128)
        elif event == 'coalition_20251120':
            ocr = DALPtOcr(DAL_PT_OCR, name='OCR_PT', letter=(255, 213, 69), threshold=128)
        elif event == 'coalition_20260122':
            ocr = Digit(FASHION_PT_OCR, name='OCR_PT', letter=(41, 40, 40), threshold=128)
        else:
            logger.error(f'ocr object is not defined in event {event}')
            raise ScriptError

        pt = 0
        for _ in self.loop(timeout=1.5):
            pt = ocr.ocr(self.device.image)
            # 999999 seems to be a default value, wait
            if pt not in [999999]:
                break
        else:
            logger.warning('Wait PT timeout, assume it is')

        return pt

    @property
    def _coalition_has_oil_icon(self):
        """
        Game devs are too asshole to drop oil display for UI design
        https://github.com/LmeSzinc/AzurLaneAutoScript/issues/5214
        """
        if self.config.Campaign_Event == 'coalition_20260122':
            return False
        return True

    def triggered_stop_condition(self, oil_check=False, pt_check=False):
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
        # Oil limit in current page
        if oil_check:
            if self.get_oil() < max(500, self.config.StopCondition_OilLimit):
                logger.hr('Triggered stop condition: Oil limit')
                self.config.task_delay(minute=(120, 240))
                return True
        # Event limit
        if pt_check:
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
        try:
            self.emotion.check_reduce(battle=self.coalition_get_battles(event, stage))
        except ScriptEnd:
            self.coalition_map_exit(event)
            raise

        if self._coalition_has_oil_icon and self.triggered_stop_condition(oil_check=True):
            self.coalition_map_exit(event)
            raise ScriptEnd

        self.enter_map(event=event, stage=stage, mode=fleet)
        self.coalition_combat()

    @staticmethod
    def handle_stage_name(event, stage):
        stage = re.sub('[ \t\n]', '', str(stage)).lower()
        if event == 'coalition_20230323':
            stage = stage.replace('-', '')

        return event, stage

    def run(self, event='', mode='', fleet='', total=0):
        event = event if event else self.config.Campaign_Event
        mode = mode if mode else self.config.Coalition_Mode
        fleet = fleet if fleet else self.config.Coalition_Fleet
        if not event or not mode or not fleet:
            raise ScriptError(f'Coalition arguments unfilled. name={event}, mode={mode}, fleet={fleet}')

        event, mode = self.handle_stage_name(event, mode)
        self.run_count = 0
        self.run_limit = self.config.StopCondition_RunCount
        while 1:
            # End
            if total and self.run_count == total:
                break
            if self.event_time_limit_triggered():
                self.config.task_stop()

            # Log
            logger.hr(f'{event}_{mode}', level=2)
            if self.config.StopCondition_RunCount > 0:
                logger.info(f'Count remain: {self.config.StopCondition_RunCount}')
            else:
                logger.info(f'Count: {self.run_count}')

            # UI switches
            if not self._coalition_has_oil_icon:
                self.ui_goto(page_campaign_menu)
                if self.triggered_stop_condition(oil_check=True):
                    break
            self.device.stuck_record_clear()
            self.device.click_record_clear()
            self.ui_goto_coalition()
            self.disable_event_on_raid()
            self.coalition_ensure_mode(event, 'battle')

            # End
            if self.triggered_stop_condition(pt_check=True):
                break

            # Run
            self.device.stuck_record_clear()
            self.device.click_record_clear()
            try:
                self.coalition_execute_once(event=event, stage=mode, fleet=fleet)
            except ScriptEnd as e:
                logger.hr('Script end')
                logger.info(str(e))
                break

            # After run
            self.run_count += 1
            if self.config.StopCondition_RunCount:
                self.config.StopCondition_RunCount -= 1
            # End
            if self.triggered_stop_condition(pt_check=True):
                break
            # Scheduler
            if self.config.task_switched():
                self.config.task_stop()


if __name__ == '__main__':
    self = Coalition('alas5', task='Coalition')
    self.device.screenshot()
    self.get_event_pt()
