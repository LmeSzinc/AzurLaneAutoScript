import numpy as np

from module.base.timer import Timer
from module.combat.assets import *
from module.combat.combat_auto import CombatAuto
from module.combat.combat_manual import CombatManual
from module.combat.emotion import Emotion
from module.combat.hp_balancer import HPBalancer
from module.combat.level import Level
from module.combat.submarine import SubmarineCall
from module.handler.auto_search import AutoSearchHandler
from module.logger import logger
from module.map.assets import MAP_OFFENSIVE
from module.retire.retirement import Retirement
from module.template.assets import TEMPLATE_COMBAT_LOADING
from module.ui.assets import BACK_ARROW


class Combat(Level, HPBalancer, Retirement, SubmarineCall, CombatAuto, CombatManual, AutoSearchHandler):
    _automation_set_timer = Timer(1)
    _emotion: Emotion
    battle_status_click_interval = 0

    @property
    def emotion(self):
        if not hasattr(self, '_emotion'):
            self._emotion = Emotion(config=self.config)
        return self._emotion

    def combat_appear(self):
        """
        Returns:
            bool: If enter combat.
        """
        if self.config.ENABLE_MAP_FLEET_LOCK and not self.is_in_map():
            if self.is_combat_loading():
                return True

        if self.appear(BATTLE_PREPARATION):
            return True
        if self.appear(BATTLE_PREPARATION_WITH_OVERLAY) and self.handle_combat_automation_confirm():
            return True

        return False

    def map_offensive(self):
        while 1:
            self.device.screenshot()

            if self.appear_then_click(MAP_OFFENSIVE, interval=1):
                continue
            if self.handle_combat_low_emotion():
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
        similarity, location = TEMPLATE_COMBAT_LOADING.match_result(self.device.image.crop((0, 620, 1280, 720)))
        if similarity > 0.85:
            loading = (location[0] + 38 - LOADING_BAR.area[0]) / (LOADING_BAR.area[2] - LOADING_BAR.area[0])
            logger.attr('Loading', f'{int(loading * 100)}%')
            return True
        else:
            return False

    def is_combat_executing(self):
        """
        Returns:
            bool:
        """
        return self.appear(PAUSE) and np.max(self.image_area(PAUSE_DOUBLE_CHECK)) < 153

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

        if emotion_reduce:
            self.emotion.wait(fleet=fleet_index)
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
            if self.appear_then_click(BATTLE_PREPARATION, interval=2):
                continue
            if self.handle_combat_automation_confirm():
                continue
            if self.handle_story_skip():
                continue

            # End
            if self.is_combat_executing():
                if emotion_reduce:
                    self.emotion.reduce(fleet_index)
                break

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
            if np.min(np.array(self.hp)[np.array(self.hp) > 0.001]) < self.config.EMERGENCY_REPAIR_SINGLE_THRESHOLD \
                    or np.max(self.hp[:3]) < self.config.EMERGENCY_REPAIR_HOLE_THRESHOLD \
                    or np.max(self.hp[3:]) < self.config.EMERGENCY_REPAIR_HOLE_THRESHOLD:
                logger.info('Use emergency repair')
                self.device.click(EMERGENCY_REPAIR_AVAILABLE)
                return True

        return False

    def combat_execute(self, auto='combat_auto', call_submarine_at_boss=False, save_get_items=False):
        """
        Args:
            auto (str): Combat auto mode.
            call_submarine_at_boss (bool):
            save_get_items (bool)
        """
        logger.info('Combat execute')
        self.submarine_call_reset()
        self.combat_auto_reset()
        self.combat_manual_reset()
        confirm_timer = Timer(10)
        confirm_timer.start()
        self.device.screenshot_interval_set(self.config.COMBAT_SCREENSHOT_INTERVAL)

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
            if call_submarine_at_boss:
                pass
            else:
                if self.handle_submarine_call():
                    continue

            # End
            if self.handle_battle_status(save_get_items=save_get_items) \
                    or self.handle_get_items(save_get_items=save_get_items):
                self.device.screenshot_interval_set(0)
                break

    def handle_battle_status(self, save_get_items=False):
        """
        Args:
            save_get_items (bool):

        Returns:
            bool:
        """
        if self.is_combat_executing():
            return False
        if self.appear_then_click(BATTLE_STATUS_S, screenshot=save_get_items, genre='status',
                                  interval=self.battle_status_click_interval):
            if not save_get_items:
                self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(BATTLE_STATUS_A, screenshot=save_get_items, genre='status',
                                  interval=self.battle_status_click_interval):
            logger.warning('Battle status A')
            self.device.send_notification('Battle finished', 'Battle status: A')
            if not save_get_items:
                self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(BATTLE_STATUS_B, screenshot=save_get_items, genre='status',
                                  interval=self.battle_status_click_interval):
            logger.warning('Battle Status B')
            self.device.send_notification('Battle finished', 'Battle status: B')
            if not save_get_items:
                self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(BATTLE_STATUS_C, screenshot=save_get_items, genre='status',
                                  interval=self.battle_status_click_interval):
            logger.warning('Battle Status C')
            self.device.send_notification('Battle finished', 'Battle status: C')
            # raise GameStuckError('Battle status C')
        if self.appear_then_click(BATTLE_STATUS_D, screenshot=save_get_items, genre='status',
                                  interval=self.battle_status_click_interval):
            logger.warning('Battle Status D')
            self.device.send_notification('Battle finished', 'Battle status: D')
            # raise GameStuckError('Battle Status D')

        return False

    def handle_get_items(self, save_get_items=False):
        """
        Args:
            save_get_items (bool):

        Returns:
            bool:
        """
        if self.appear_then_click(GET_ITEMS_1, screenshot=save_get_items, genre='get_items', offset=5,
                                  interval=self.battle_status_click_interval):
            self.interval_reset(BATTLE_STATUS_S)
            self.interval_reset(BATTLE_STATUS_A)
            self.interval_reset(BATTLE_STATUS_B)
            return True
        if self.appear_then_click(GET_ITEMS_2, screenshot=save_get_items, genre='get_items', offset=5,
                                  interval=self.battle_status_click_interval):
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

    def handle_get_ship(self, save_get_items=False):
        """
        Args:
            save_get_items (bool):

        Returns:
            bool:
        """
        if self.appear_then_click(GET_SHIP, screenshot=save_get_items, genre='get_ship'):
            if self.appear(NEW_SHIP, interval=1):
                logger.info('Get a new SHIP')
                self.config.GET_SHIP_TRIGGERED = True
            return True

        return False

    def combat_status(self, save_get_items=False, expected_end=None):
        """
        Args:
            save_get_items (bool):
            expected_end (str, callable): with_searching, no_searching, in_stage.
        """
        logger.info('Combat status')
        logger.attr('expected_end', expected_end.__name__ if callable(expected_end) else expected_end)
        exp_info = False  # This is for the white screen bug in game
        while 1:
            self.device.screenshot()

            # Combat status
            if not exp_info and self.handle_get_ship(save_get_items=save_get_items):
                continue
            if self.handle_get_items(save_get_items=save_get_items):
                continue
            if self.handle_battle_status(save_get_items=save_get_items):
                continue
            if self.handle_popup_confirm('combat_status'):
                continue
            if self.handle_exp_info():
                exp_info = True
                continue
            if self.handle_urgent_commission(save_get_items=save_get_items):
                continue
            if self.handle_story_skip():
                continue
            if self.handle_guild_popup_cancel():
                continue

            # End
            if self.handle_in_stage():
                break
            if expected_end is None:
                if self.handle_in_map_with_enemy_searching():
                    break
            if isinstance(expected_end, str):
                if expected_end == 'in_stage' and self.handle_in_stage():
                    break
                if expected_end == 'with_searching' and self.handle_in_map_with_enemy_searching():
                    break
                if expected_end == 'no_searching' and self.handle_in_map_no_enemy_searching():
                    break
                if expected_end == 'in_ui' and self.appear(BACK_ARROW, offset=(20, 20)):
                    break
            if callable(expected_end):
                if expected_end():
                    break

    def combat(self, balance_hp=None, emotion_reduce=None, auto_mode=None, call_submarine_at_boss=None,
               save_get_items=None, expected_end=None, fleet_index=1):
        """
        Execute a combat.
        """
        balance_hp = balance_hp if balance_hp is not None else self.config.ENABLE_HP_BALANCE
        emotion_reduce = emotion_reduce if emotion_reduce is not None else self.config.ENABLE_EMOTION_REDUCE
        if auto_mode is None:
            auto_mode = self.config.FLEET_1_AUTO_MODE if fleet_index == 1 else self.config.FLEET_2_AUTO_MODE
        call_submarine_at_boss = call_submarine_at_boss if call_submarine_at_boss is not None else self.config.SUBMARINE_CALL_AT_BOSS
        save_get_items = save_get_items if save_get_items is not None else self.config.ENABLE_SAVE_GET_ITEMS
        self.battle_status_click_interval = 7 if save_get_items else 0

        # if not hasattr(self, 'emotion'):
        #     self.emotion = Emotion(config=self.config)

        self.combat_preparation(
            balance_hp=balance_hp, emotion_reduce=emotion_reduce, auto=auto_mode, fleet_index=fleet_index)
        self.combat_execute(
            auto=auto_mode, call_submarine_at_boss=call_submarine_at_boss, save_get_items=save_get_items)
        self.combat_status(
            save_get_items=save_get_items, expected_end=expected_end)
        self.handle_map_after_combat_story()

        logger.info('Combat end.')
