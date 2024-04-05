import numpy as np

from module.base.utils import get_color
from module.combat.assets import BATTLE_PREPARATION
from module.combat.combat import Combat
from module.daily.assets import *
from module.daily.equipment import DailyEquipment
from module.logger import logger
from module.ocr.ocr import Digit
from module.ui.assets import BACK_ARROW, DAILY_CHECK
from module.ui.page import page_campaign_menu, page_daily

DAILY_MISSION_LIST = [DAILY_MISSION_1, DAILY_MISSION_2, DAILY_MISSION_3]
OCR_REMAIN = Digit(OCR_REMAIN, threshold=128, alphabet='01234')
OCR_DAILY_FLEET_INDEX = Digit(OCR_DAILY_FLEET_INDEX, letter=(90, 154, 255), threshold=128, alphabet='123456')


class Daily(Combat, DailyEquipment):
    daily_current: int
    daily_checked: list
    emergency_module_development = False

    def is_active(self):
        color = get_color(image=self.device.image, area=DAILY_ACTIVE.area)
        color = np.array(color).astype(float)
        color = (np.max(color) + np.min(color)) / 2
        active = color > 30
        if active:
            logger.attr(f'Daily_{self.daily_current}', 'active')
        else:
            logger.attr(f'Daily_{self.daily_current}', 'inactive')
        return active

    def _wait_daily_switch(self):
        self.device.sleep((1, 1.2))

    def next(self):
        self.daily_current += 1
        logger.info('Switch to %s' % str(self.daily_current))
        self.device.click(DAILY_NEXT)
        self._wait_daily_switch()
        self.device.screenshot()

    def prev(self):
        self.daily_current -= 1
        logger.info('Switch to %s' % str(self.daily_current))
        self.device.click(DAILY_PREV)
        self._wait_daily_switch()
        self.device.screenshot()

    def handle_daily_additional(self):
        if self.handle_guild_popup_cancel():
            return True
        return False

    def get_daily_stage_and_fleet(self):
        """
        Returns:
            int: Stage index, 0 to 3
            int: Fleet index, 1 to 6
        """
        if self.emergency_module_development:
            # Meaning of daily_current
            # 1 Emergency Module Development 限时兵装训练
            # 2 Escort Mission 商船护送
            # 3 Advance Mission 海域突进
            # 4 Fierce Assault 斩首行动
            # 5 Tactical Training 战术研修
            # 6 Supply Line Disruption 破交作战
            # 7 Module Development 兵装训练
            fleets = [
                0,
                self.config.Daily_EmergencyModuleDevelopmentFleet,
                self.config.Daily_EscortMissionFleet,
                self.config.Daily_AdvanceMissionFleet,
                self.config.Daily_FierceAssaultFleet,
                self.config.Daily_TacticalTrainingFleet,
                0,  # Supply Line Disruption, which needs to be done manually or to be done by daily skip
                self.config.Daily_ModuleDevelopmentFleet,
                0
            ]
            stages = [
                0,
                self.config.Daily_EmergencyModuleDevelopment,
                self.config.Daily_EscortMission,
                self.config.Daily_AdvanceMission,
                self.config.Daily_FierceAssault,
                self.config.Daily_TacticalTraining,
                self.config.Daily_SupplyLineDisruption,
                self.config.Daily_ModuleDevelopment,
                0
            ]
        else:
            # Meaning of daily_current
            # 1 Tactical Training 战术研修
            # 2 Supply Line Disruption 破交作战
            # 3 Module Development 兵装训练
            # 4 (not open)
            # 5 Escort Mission 商船护送
            # 6 Advance Mission 海域突进
            # 7 Fierce Assault 斩首行动
            fleets = [
                0,
                self.config.Daily_TacticalTrainingFleet,
                0,  # Supply Line Disruption, which needs to be done manually or to be done by daily skip
                self.config.Daily_ModuleDevelopmentFleet,
                0,  # Empty
                self.config.Daily_EscortMissionFleet,
                self.config.Daily_AdvanceMissionFleet,
                self.config.Daily_FierceAssaultFleet,
                0
            ]
            stages = [
                0,
                self.config.Daily_TacticalTraining,
                self.config.Daily_SupplyLineDisruption,
                self.config.Daily_ModuleDevelopment,
                0,  # Empty
                self.config.Daily_EscortMission,
                self.config.Daily_AdvanceMission,
                self.config.Daily_FierceAssault,
                0
            ]
        dic = {
            'skip': 0,
            'first': 1,
            'second': 2,
            'third': 3,
        }
        fleet = fleets[self.daily_current]
        stage = stages[self.daily_current]

        if stage not in dic:
            logger.warning(f'Unknown daily stage `{stage}` from daily_current={self.daily_current}')
        stage = dic.get(stage, 0)
        return int(stage), int(fleet)

    @property
    def supply_line_disruption_index(self):
        if self.emergency_module_development:
            return 2
        else:
            return 2

    @property
    def empty_index(self):
        if self.emergency_module_development:
            return 4
        else:
            return 4

    def daily_execute(self, remain=3, stage=1, fleet=1):
        """
        Args:
            remain (int): Remain daily challenge count.
            stage (int): Index of stage counted from top, 1 to 3.
            fleet (int): Index of fleet to use.

        Returns:
            bool: True if success, False if daily locked.

        Pages:
            in: page_daily
            out: page_daily
        """
        logger.hr(f'Daily {self.daily_current}', level=2)
        logger.info(f'remain={remain}, stage={stage}, fleet={fleet}')

        def daily_enter_check():
            return self.appear(DAILY_ENTER_CHECK, threshold=30)

        def daily_end():
            if self.appear(BATTLE_PREPARATION, offset=(20, 20), interval=2):
                self.device.click(BACK_ARROW)
            return self.appear(DAILY_ENTER_CHECK, threshold=30) or self.appear(BACK_ARROW, offset=(30, 30))

        self.ui_click(click_button=DAILY_ENTER, check_button=daily_enter_check, appear_button=DAILY_CHECK,
                      skip_first_screenshot=True)
        if self.appear(DAILY_LOCKED):
            logger.info('Daily locked')
            self.ui_click(click_button=BACK_ARROW, check_button=DAILY_CHECK)
            self.device.sleep((1, 1.2))
            return False

        button = DAILY_MISSION_LIST[stage - 1]
        for n in range(remain):
            logger.hr(f'Count {n + 1}')
            result = self.daily_enter(button)
            if not result:
                break
            if self.daily_current == self.supply_line_disruption_index:
                logger.info('Submarine daily skip not unlocked, skip')
                self.ui_click(click_button=BACK_ARROW, check_button=daily_enter_check, skip_first_screenshot=True)
                break
            # Execute classic daily run
            self.ui_ensure_index(fleet, letter=OCR_DAILY_FLEET_INDEX, prev_button=DAILY_FLEET_PREV,
                                 next_button=DAILY_FLEET_NEXT, fast=False, skip_first_screenshot=True)
            self.combat(emotion_reduce=False, save_get_items=False, expected_end=daily_end, balance_hp=False)

        self.ui_click(click_button=BACK_ARROW, check_button=DAILY_CHECK, additional=self.handle_daily_additional,
                      skip_first_screenshot=True)
        self.device.sleep((1, 1.2))
        return True

    def daily_enter(self, button, skip_first_screenshot=True):
        """
        Args:
            button (Button): Daily entrance
            skip_first_screenshot (bool):

        Returns:
            bool: True if combat appear. False if daily skip unlocked, skipped daily, received rewards.

        Pages:
            in: DAILY_ENTER_CHECK
            out: DAILY_ENTER_CHECK or combat_appear
        """
        reward_received = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(DAILY_ENTER_CHECK, threshold=30, interval=5):
                self.device.click(button)
                continue
            if self.handle_get_items():
                reward_received = True
                continue
            if self.config.Daily_UseDailySkip:
                if self.appear_then_click(DAILY_SKIP, offset=(20, 20), interval=5):
                    continue
            else:
                if self.appear_then_click(DAILY_NORMAL_RUN, offset=(20, 20), interval=5):
                    continue
            if self.handle_combat_automation_confirm():
                continue
            if self.handle_daily_additional():
                continue
            if self.handle_popup_confirm('DAILY_SKIP'):
                continue

            # End
            if self.appear(DAILY_SKIP, offset=(20, 20)):
                if reward_received:
                    return False
                if self.info_bar_count():
                    return False
            if self.appear(DAILY_ENTER_CHECK, threshold=30):
                if self.info_bar_count():
                    return False
            if self.combat_appear():
                return True

    def daily_check(self, n=None):
        if not n:
            n = self.daily_current
        self.daily_checked.append(n)
        logger.info(f'Checked daily {n}')
        logger.info(f'Checked_list: {self.daily_checked}')

    def daily_run_one(self):
        logger.hr('Daily run one', level=1)
        self.ui_ensure(page_daily)
        self.device.sleep(0.2)
        self.device.screenshot()
        self.daily_current = 1
        self.emergency_module_development = self.appear(ENTRANCE_EMERGENCY_MODULE_DEVELOPMENT, offset=(25, 50))
        logger.attr('emergency_module_development', self.emergency_module_development)

        logger.info(f'Checked_list: {self.daily_checked}')
        for _ in range(max(self.daily_checked)):
            self.next()

        while 1:
            if self.daily_current > 7:
                break
            if self.daily_current == self.empty_index:
                logger.info('This daily is not open now')
                self.daily_check()
                self.next()
                continue
            stage, fleet = self.get_daily_stage_and_fleet()
            if self.daily_current == self.supply_line_disruption_index and not self.config.Daily_UseDailySkip:
                logger.info('Skip supply line disruption if UseDailySkip disabled')
                self.daily_check()
                self.next()
                continue
            if not stage:
                logger.info(f'No stage set on daily_current: {self.daily_current}, skip')
                self.daily_check()
                self.next()
                continue
            if self.daily_current != self.supply_line_disruption_index and not fleet:
                logger.info(f'No fleet set on daily_current: {self.daily_current}, skip')
                self.daily_check()
                self.next()
                continue
            if not self.is_active():
                self.daily_check()
                self.next()
                continue
            remain = OCR_REMAIN.ocr(self.device.image)
            if remain == 0:
                self.daily_check()
                self.next()
                continue
            else:
                self.daily_execute(remain=remain, stage=stage, fleet=fleet)
                self.daily_check()
                # The order of daily tasks will be disordered after execute a daily, exit and re-enter to reset.
                # 打完一次之后每日任务的顺序会乱掉, 退出再进入来重置顺序.
                self.ui_goto(page_campaign_menu)
                break

    def daily_run(self):
        self.daily_checked = [0]

        while 1:
            self.daily_run_one()

            if self.emergency_module_development and self.config.Daily_EmergencyModuleDevelopment != 'skip':
                self.daily_checked = [0]

            if max(self.daily_checked) >= 7:
                logger.info('Daily clear complete.')
                break

    def run(self):
        """
        Pages:
            in: Any page
            out: page_daily
        """
        # self.equipment_take_on()
        self.daily_run()
        # self.equipment_take_off()

        # Cannot stay in page_daily, because order is disordered.
        self.config.task_delay(server_update=True)
