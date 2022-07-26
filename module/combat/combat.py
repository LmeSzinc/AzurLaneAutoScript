import numpy as np

from module.base.timer import Timer
from module.combat.assets import *
from module.combat.combat_auto import CombatAuto
from module.combat.combat_manual import CombatManual
from module.combat.hp_balancer import HPBalancer
from module.combat.level import Level
from module.combat.submarine import SubmarineCall
from module.handler.auto_search import AutoSearchHandler
from module.logger import logger
from module.map.assets import MAP_OFFENSIVE
from module.retire.retirement import Retirement
from module.statistics.azurstats import DropImage
from module.template.assets import TEMPLATE_COMBAT_LOADING
from module.ui.assets import BACK_ARROW


class Combat(Level, HPBalancer, Retirement, SubmarineCall, CombatAuto, CombatManual, AutoSearchHandler):
    _automation_set_timer = Timer(1)
    battle_status_click_interval = 0

    def combat_appear(self):
        """
        Returns:
            bool: If enter combat.
        """
        if self.config.Campaign_UseFleetLock and not self.is_in_map():
            if self.is_combat_loading():
                return True

        if self.appear(BATTLE_PREPARATION):
            return True
        if self.appear(BATTLE_PREPARATION_WITH_OVERLAY) and self.handle_combat_automation_confirm():
            return True

        return False

    def map_offensive(self, skip_first_screenshot=True):
        """
        Pages:
            in: in_map, MAP_OFFENSIVE
            out: combat_appear
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(MAP_OFFENSIVE, interval=1):
                continue
            if self.handle_combat_low_emotion():
                self.interval_reset(MAP_OFFENSIVE)
                continue
            if self.handle_retirement():
                continue

            # Break
            if self.combat_appear():
                break

    def is_combat_loading(self):
        """
        Returns:
            bool:
        """
        similarity, button = TEMPLATE_COMBAT_LOADING.match_result(self.image_crop((0, 620, 1280, 720)))
        if similarity > 0.85:
            loading = (button.area[0] + 38 - LOADING_BAR.area[0]) / (LOADING_BAR.area[2] - LOADING_BAR.area[0])
            logger.attr('Loading', f'{int(loading * 100)}%')
            return True
        else:
            return False

    def is_combat_executing(self):
        """
        Returns:
            bool:
        """
        return self.appear(PAUSE) and np.max(self.image_crop(PAUSE_DOUBLE_CHECK)) < 153

    def ensure_combat_oil_loaded(self):
        self.wait_until_stable(COMBAT_OIL_LOADING)

    def handle_combat_automation_confirm(self):
        if self.appear(AUTOMATION_CONFIRM_CHECK, interval=1):
            self.appear_then_click(AUTOMATION_CONFIRM, offset=True)
            return True

        return False

    def combat_preparation(self, balance_hp=False, emotion_reduce=False, auto='combat_auto', fleet_index=1):
        """
        Args:
            balance_hp (bool):
            emotion_reduce (bool):
            auto (str):
            fleet_index (int):
        """
        logger.info('Combat preparation.')
        skip_first_screenshot = True
        interval_set = False

        if emotion_reduce:
            self.emotion.wait(fleet_index=fleet_index)
        if balance_hp:
            self.hp_balance()

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(BATTLE_PREPARATION):
                if self.handle_combat_automation_set(auto=auto == 'combat_auto'):
                    continue
            if self.handle_retirement():
                continue
            if self.handle_combat_low_emotion():
                continue
            if balance_hp and self.handle_emergency_repair_use():
                continue
            if self.handle_battle_preparation():
                continue
            if self.handle_combat_automation_confirm():
                continue
            if self.handle_story_skip():
                continue
            if not interval_set:
                if self.is_combat_loading():
                    self.device.screenshot_interval_set('combat')
                    interval_set = True

            # End
            if self.is_combat_executing():
                if emotion_reduce:
                    self.emotion.reduce(fleet_index)
                break

    def handle_battle_preparation(self):
        """
        Returns:
            bool:
        """
        if self.appear_then_click(BATTLE_PREPARATION, interval=2):
            return True

        return False

    def handle_combat_automation_set(self, auto):
        """
        Args:
            auto (bool): If use auto.

        Returns:
            bool:
        """
        if not self._automation_set_timer.reached():
            return False

        if self.appear(AUTOMATION_ON):
            logger.info('[Automation] ON')
            if not auto:
                self.device.click(AUTOMATION_SWITCH)
                self.device.sleep(1)
                self._automation_set_timer.reset()
                return True

        if self.appear(AUTOMATION_OFF):
            logger.info('[Automation] OFF')
            if auto:
                self.device.click(AUTOMATION_SWITCH)
                self.device.sleep(1)
                self._automation_set_timer.reset()
                return True

        if self.appear_then_click(AUTOMATION_CONFIRM, offset=True):
            self._automation_set_timer.reset()
            return True

        return False

    def handle_emergency_repair_use(self):
        if not self.config.HpControl_UseEmergencyRepair:
            return False

        if self.appear_then_click(EMERGENCY_REPAIR_CONFIRM, offset=True):
            return True
        if self.appear(BATTLE_PREPARATION) and self.appear(EMERGENCY_REPAIR_AVAILABLE):
            # When entering battle_preparation page (or after emergency repairing),
            # the emergency icon is active by default, even if nothing to use.
            # After a short animation, everything shows as usual.
            # Using fleet power number as a stable checker.
            # First wait for it to be non-zero, then wait for it to be stable.
            self.wait_until_disappear(MAIN_FLEET_POWER_ZERO, offset=(20, 20))
            stable_checker = Button(
                area=MAIN_FLEET_POWER_ZERO.area, color=(), button=MAIN_FLEET_POWER_ZERO.button, name='STABLE_CHECKER')
            self.wait_until_stable(stable_checker)
            if not self.appear(EMERGENCY_REPAIR_AVAILABLE):
                return False
            logger.info('EMERGENCY_REPAIR_AVAILABLE')
            if not len(self.hp):
                return False
            if np.min(np.array(self.hp)[np.array(self.hp) > 0.001]) < self.config.HpControl_RepairUseSingleThreshold \
                    or np.max(self.hp[:3]) < self.config.HpControl_RepairUseMultiThreshold \
                    or np.max(self.hp[3:]) < self.config.HpControl_RepairUseMultiThreshold:
                logger.info('Use emergency repair')
                self.device.click(EMERGENCY_REPAIR_AVAILABLE)
                return True

        return False

    def combat_execute(self, auto='combat_auto', submarine='do_not_use', drop=None):
        """
        Args:
            auto (str): ['combat_auto', 'combat_manual', 'stand_still_in_the_middle', 'hide_in_bottom_left']
            submarine (str): ['do_not_use', 'hunt_only', 'every_combat']
            drop (DropImage):
        """
        logger.info('Combat execute')
        self.submarine_call_reset()
        self.combat_auto_reset()
        self.combat_manual_reset()
        self.device.click_record_clear()
        confirm_timer = Timer(10)
        confirm_timer.start()

        while 1:
            self.device.screenshot()

            if not confirm_timer.reached() and self.appear_then_click(AUTOMATION_CONFIRM, offset=True):
                continue

            if self.handle_story_skip():
                continue
            if self.handle_combat_auto(auto):
                continue
            if self.handle_combat_manual(auto):
                continue
            if auto != 'combat_auto' and self.auto_mode_checked and self.is_combat_executing():
                if self.handle_combat_weapon_release():
                    continue
            if self.handle_submarine_call(submarine):
                continue
            if self.handle_popup_confirm('COMBAT_EXECUTE'):
                continue

            # End
            if self.handle_battle_status(drop=drop) \
                    or self.handle_get_items(drop=drop):
                self.device.screenshot_interval_set()
                break

    def handle_battle_status(self, drop=None):
        """
        Args:
            drop (DropImage):

        Returns:
            bool:
        """
        if self.is_combat_executing():
            return False
        if self.appear(BATTLE_STATUS_S, interval=self.battle_status_click_interval):
            if drop:
                drop.handle_add(self)
            else:
                self.device.sleep((0.25, 0.5))
            self.device.click(BATTLE_STATUS_S)
            return True
        if self.appear(BATTLE_STATUS_A, interval=self.battle_status_click_interval):
            logger.warning('Battle status A')
            if drop:
                drop.handle_add(self)
            else:
                self.device.sleep((0.25, 0.5))
            self.device.click(BATTLE_STATUS_A)
            return True
        if self.appear(BATTLE_STATUS_B, interval=self.battle_status_click_interval):
            logger.warning('Battle Status B')
            if drop:
                drop.handle_add(self)
            else:
                self.device.sleep((0.25, 0.5))
            self.device.click(BATTLE_STATUS_B)
            return True
        if self.appear(BATTLE_STATUS_C, interval=self.battle_status_click_interval):
            logger.warning('Battle Status C')
            # raise GameStuckError('Battle status C')
            if drop:
                drop.handle_add(self)
            else:
                self.device.sleep((0.25, 0.5))
            self.device.click(BATTLE_STATUS_C)
            return True
        if self.appear(BATTLE_STATUS_D, interval=self.battle_status_click_interval):
            logger.warning('Battle Status D')
            # raise GameStuckError('Battle Status D')
            if drop:
                drop.handle_add(self)
            else:
                self.device.sleep((0.25, 0.5))
            self.device.click(BATTLE_STATUS_D)
            return True

        return False

    def handle_get_items(self, drop=None):
        """
        Args:
            drop (DropImage):

        Returns:
            bool:
        """
        if self.appear(GET_ITEMS_1, offset=5, interval=self.battle_status_click_interval):
            if drop:
                drop.handle_add(self)
            self.device.click(GET_ITEMS_1)
            self.interval_reset(BATTLE_STATUS_S)
            self.interval_reset(BATTLE_STATUS_A)
            self.interval_reset(BATTLE_STATUS_B)
            return True
        if self.appear(GET_ITEMS_2, offset=5, interval=self.battle_status_click_interval):
            if drop:
                drop.handle_add(self)
            self.device.click(GET_ITEMS_1)
            self.interval_reset(BATTLE_STATUS_S)
            self.interval_reset(BATTLE_STATUS_A)
            self.interval_reset(BATTLE_STATUS_B)
            return True
        if self.appear(GET_ITEMS_3, offset=5, interval=self.battle_status_click_interval):
            if drop:
                drop.handle_add(self)
            self.device.click(GET_ITEMS_1)
            self.interval_reset(BATTLE_STATUS_S)
            self.interval_reset(BATTLE_STATUS_A)
            self.interval_reset(BATTLE_STATUS_B)
            return True

        return False

    def handle_exp_info(self):
        """
        Returns:
            bool:
        """
        if self.is_combat_executing():
            return False
        if self.appear_then_click(EXP_INFO_S):
            self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(EXP_INFO_A):
            self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(EXP_INFO_B):
            self.device.sleep((0.25, 0.5))
            return True

        return False

    def handle_get_ship(self, drop=None):
        """
        Args:
            drop (DropImage):

        Returns:
            bool:
        """
        if self.appear_then_click(GET_SHIP, interval=1):
            if self.appear(NEW_SHIP):
                logger.info('Get a new SHIP')
                if drop:
                    drop.handle_add(self)
                self.config.GET_SHIP_TRIGGERED = True
            return True

        return False

    def combat_status(self, drop=None, expected_end=None):
        """
        Args:
            drop (DropImage):
            expected_end (str, callable): with_searching, no_searching, in_stage.
        """
        logger.info('Combat status')
        logger.attr('expected_end', expected_end.__name__ if callable(expected_end) else expected_end)
        battle_status = False
        exp_info = False  # This is for the white screen bug in game
        while 1:
            self.device.screenshot()

            # Expected end
            if isinstance(expected_end, str):
                if expected_end == 'in_stage' and self.handle_in_stage():
                    break
                if expected_end == 'with_searching' and self.handle_in_map_with_enemy_searching(drop=drop):
                    break
                if expected_end == 'no_searching' and self.handle_in_map_no_enemy_searching(drop=drop):
                    break
                if expected_end == 'in_ui' and self.appear(BACK_ARROW, offset=(20, 20)):
                    break
            if callable(expected_end):
                if expected_end():
                    break

            # Combat status
            if not exp_info and self.handle_get_ship(drop=drop):
                continue
            if self.handle_get_items(drop=drop):
                continue
            if not exp_info and self.handle_battle_status(drop=drop):
                battle_status = True
                continue
            if self.handle_popup_confirm('COMBAT_STATUS'):
                if battle_status and not exp_info:
                    logger.info('Locking a new ship')
                    self.config.GET_SHIP_TRIGGERED = True
                continue
            if self.handle_exp_info():
                exp_info = True
                continue
            if self.handle_urgent_commission(drop=drop):
                continue
            if self.handle_story_skip(drop=drop):
                continue
            if self.handle_guild_popup_cancel():
                continue
            if self.handle_vote_popup():
                continue
            if self.handle_mission_popup_ack():
                continue
            if self.handle_auto_search_exit(drop=drop):
                continue

            # End
            if self.handle_in_stage():
                break
            if expected_end is None:
                if self.handle_in_map_with_enemy_searching(drop=drop):
                    break

    def combat(self, balance_hp=None, emotion_reduce=None, auto_mode=None, submarine_mode=None,
               save_get_items=None, expected_end=None, fleet_index=1):
        """
        Execute a combat.
        Will use user config if argument is None.

        Args:
            balance_hp (bool):
            emotion_reduce (bool):
            auto_mode (str): combat_auto, combat_manual, stand_still_in_the_middle, hide_in_bottom_left
            submarine_mode (str): do_not_use, hunt_only, every_combat
            save_get_items (bool, DropImage):
            expected_end (str, callable):
            fleet_index (int): 1 or 2
        """
        balance_hp = balance_hp if balance_hp is not None else self.config.HpControl_UseHpBalance
        emotion_reduce = emotion_reduce if emotion_reduce is not None else self.config.Emotion_CalculateEmotion
        if auto_mode is None:
            auto_mode = self.config.Fleet_Fleet1Mode if fleet_index == 1 else self.config.Fleet_Fleet2Mode
        if submarine_mode is None:
            submarine_mode = 'do_not_use'
            if self.config.Submarine_Fleet:
                submarine_mode = self.config.Submarine_Mode
        self.battle_status_click_interval = 7 if save_get_items else 0

        # if not hasattr(self, 'emotion'):
        #     self.emotion = Emotion(config=self.config)

        with self.stat.new(
                genre=self.config.campaign_name, method=self.config.DropRecord_CombatRecord
        ) as drop:
            if save_get_items is False:
                drop = None
            elif isinstance(save_get_items, DropImage):
                drop = save_get_items
            self.combat_preparation(
                balance_hp=balance_hp, emotion_reduce=emotion_reduce, auto=auto_mode, fleet_index=fleet_index)
            self.combat_execute(
                auto=auto_mode, submarine=submarine_mode, drop=drop)
            self.combat_status(
                drop=drop, expected_end=expected_end)
            # self.handle_map_after_combat_story()

        logger.info('Combat end.')
