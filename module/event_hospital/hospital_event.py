from module.campaign.campaign_ui import ModeSwitch
from module.combat.assets import BATTLE_PREPARATION
from module.event_hospital.assets import *
from module.event_hospital.hospital import Hospital
from module.exception import OilExhausted, ScriptEnd, ScriptError
from module.logger import logger
from module.minigame.assets import BACK
from module.raid.assets import RAID_FLEET_PREPARATION
from module.raid.raid import raid_entrance
from module.raid.run import RaidRun
from module.ui.page import page_hospital

ASIDE_SWITCH_HOSPITAL = ModeSwitch('Aside_switch_hospital', is_selector=True)
ASIDE_SWITCH_HOSPITAL.add_state('easy', CHAPTER_HOSPITAL_EASY)
ASIDE_SWITCH_HOSPITAL.add_state('normal', CHAPTER_HOSPITAL_NORMAL)
ASIDE_SWITCH_HOSPITAL.add_state('hard', CHAPTER_HOSPITAL_HARD)


class HospitalEvent(Hospital, RaidRun):
    raid_name = 'raid_20250327'

    def campaign_ensure_aside_hospital(self, chapter):
        """
        Args:
            chapter: 'easy', 'normal', 'hard'
        """
        if chapter in ['easy', 'normal', 'hard']:
            ASIDE_SWITCH_HOSPITAL.set(chapter, main=self)
        else:
            logger.warning(f'Unknown campaign aside: {chapter}')

    def hospital_expected_end(self):
        """
        Returns:
            bool: If combat ended
        """
        if self.ui_page_appear(page_hospital, interval=2):
            return True
        if self.appear_then_click(HOSPITAL_BATTLE_EXIT, offset=(20, 20), interval=2):
            return False
        if self.appear(BATTLE_PREPARATION, offset=(30, 20), interval=2):
            logger.info(f'{BATTLE_PREPARATION} -> {BACK}')
            self.device.click(BACK)
            return False
        if self.appear(RAID_FLEET_PREPARATION, offset=(30, 30), interval=2):
            logger.info(f'{RAID_FLEET_PREPARATION} -> {BACK}')
            self.device.click(BACK)
            return False
        if self.handle_get_clue():
            return False
        return False

    def raid_enter(self, stage, raid, skip_first_screenshot=True):
        """
        Args:
            stage:
            raid:
            skip_first_screenshot:

        Pages:
            in: page_raid
            out: BATTLE_PREPARATION
        """
        entrance = raid_entrance(raid=raid, mode=stage)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(RAID_FLEET_PREPARATION, offset=(30, 30)):
                break

            if self.ui_page_appear(page_hospital):
                # Check PT when entrance appear
                if self.event_pt_limit_triggered():
                    self.config.task_stop()
                self.device.click(entrance)
                continue

            if self.appear_then_click(HOSPITAL_BATTLE_PREPARE, offset=(20, 20), interval=2):
                continue

            if self.handle_get_clue():
                continue

    def raid_execute_once(self, mode, raid, stage):
        """
        Args:
            mode:
            raid:

        Returns:
            in: page_raid
            out: page_raid
        """
        logger.hr('Raid Execute')
        self.config.override(
            Campaign_Event=raid,
            Campaign_Name=f'{raid}_{mode}_{stage}',
            Campaign_UseAutoSearch=False,
            Fleet_FleetOrder='fleet1_all_fleet2_standby',
            Hospital_UseRecommendFleet=False,
        )

        self.emotion.check_reduce(1)

        self.raid_enter(stage=stage, raid=raid)
        self.hospital_combat()

        logger.hr('Raid End')

    def run(self, name='', mode='', stage='', total=0):
        """
        Args:
            name (str): Raid name, such as 'raid_20200624'
            mode (str): Raid mode, such as 'hard', 'normal', 'easy'
            stage (str): Raid stage, such as 'T1', 'T2'
            total (int): Total run count
        """
        name = name if name else self.raid_name
        mode = mode if mode else self.config.HospitalEvent_Mode
        stage = stage if stage else self.config.HospitalEvent_Stage
        if not name or not mode or not stage:
            raise ScriptError(f'RaidRun arguments unfilled. name={name}, mode={mode}, stage={stage}')

        self.run_count = 0
        self.run_limit = self.config.StopCondition_RunCount
        while 1:
            # End
            if total and self.run_count == total:
                break
            if self.event_time_limit_triggered():
                self.config.task_stop()

            # Log
            logger.hr(f'{name}_{mode}_{stage}', level=2)
            if self.config.StopCondition_RunCount > 0:
                logger.info(f'Count remain: {self.config.StopCondition_RunCount}')
            else:
                logger.info(f'Count: {self.run_count}')

            # End
            if self.triggered_stop_condition():
                break

            # UI ensure
            self.device.stuck_record_clear()
            self.device.click_record_clear()
            self.ui_ensure(page_hospital)

            # Run
            self.device.stuck_record_clear()
            self.device.click_record_clear()
            try:
                self.campaign_ensure_aside_hospital(chapter=mode)
                self.raid_execute_once(mode=mode, raid=name, stage=stage)
            except OilExhausted:
                logger.hr('Triggered stop condition: Oil limit')
                self.config.task_delay(minute=(120, 240))
                break
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
