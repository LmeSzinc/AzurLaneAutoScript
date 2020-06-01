import numpy as np

from module.base.timer import Timer
from module.base.utils import color_bar_percentage
from module.combat.assets import *
from module.combat.combat_auto import CombatAuto
from module.combat.combat_manual import CombatManual
from module.combat.emotion import Emotion
from module.combat.hp_balancer import HPBalancer
from module.combat.submarine import SubmarineCall
from module.handler.enemy_searching import EnemySearchingHandler
from module.logger import logger
from module.map.assets import MAP_OFFENSIVE
from module.retire.retirement import Retirement
from module.ui.assets import BACK_ARROW


class Combat(HPBalancer, EnemySearchingHandler, Retirement, SubmarineCall, CombatAuto, CombatManual):
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
        left = color_bar_percentage(self.device.image, area=LOADING_BAR.area, prev_color=(99, 150, 255))
        right = color_bar_percentage(self.device.image, area=LOADING_BAR.area, prev_color=(225, 225, 225), reverse=True)
        if 0.15 < left < 0.95 and right > 0.15 and left + right <= 1.2:
            logger.attr('Loading', f'{int(left * 100)}%({int(right * 100)}%)')
            return True

        return False

    def is_combat_executing(self):
        """
        Returns:
            bool:
        """
        return self.appear(PAUSE) and np.max(self.device.image.crop(PAUSE_DOUBLE_CHECK.area)) < 153

    def handle_combat_automation_confirm(self):
        if self.appear(AUTOMATION_CONFIRM_CHECK, interval=1):
            self.appear_then_click(AUTOMATION_CONFIRM, offset=True)
            return True

        return False

    def combat_preparation(self, balance_hp=False, emotion_reduce=False, auto=True, fleet_index=1):
        """
        Args:
            balance_hp (bool):
            emotion_reduce (bool):
            auto (bool):
            fleet_index (int):
        """
        logger.info('Combat preparation.')

        if emotion_reduce:
            self.emotion.wait(fleet=fleet_index)
        if balance_hp:
            self.hp_balance()

        while 1:
            self.device.screenshot()

            if self.appear(BATTLE_PREPARATION):
                if self.handle_combat_automation_set(auto=auto):
                    continue
            if self.handle_retirement():
                if self.config.ENABLE_HP_BALANCE:
                    self.wait_until_appear(BATTLE_PREPARATION)
                    # When re-entering battle_preparation page, the emergency icon is active by default, even if
                    # nothing to use. After a short animation, everything shows as usual.
                    self.device.sleep(0.5)  # Wait animation.
                    continue
            if self.handle_combat_low_emotion():
                continue
            if self.handle_emergency_repair_use():
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
        if not self.config.ENABLE_HP_BALANCE:
            return False
        if self.appear_then_click(EMERGENCY_REPAIR_CONFIRM, offset=True):
            self.device.sleep(0.5)  # Animation: hp increase and emergency_repair amount decrease.
            return True
        if self.appear(BATTLE_PREPARATION) and self.appear(EMERGENCY_REPAIR_AVAILABLE):
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

    def combat_execute(self, auto=True, call_submarine_at_boss=False, save_get_items=False):
        """
        Args:
            auto (bool):
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
            if self.handle_combat_auto():
                continue
            if self.handle_combat_manual():
                continue
            if not auto and self.is_combat_executing():
                if self.handle_combat_weapon_release():
                    continue
            if call_submarine_at_boss:
                pass
            else:
                if self.handle_submarine_call():
                    continue

            # End
            if self.handle_battle_status(save_get_items=save_get_items):
                self.device.screenshot_interval_set(0)
                break

    def handle_battle_status(self, save_get_items=False):
        """
        Args:
            save_get_items (bool):

        Returns:
            bool:
        """
        if self.appear_then_click(BATTLE_STATUS_S, screenshot=save_get_items, genre='status',
                                  interval=self.battle_status_click_interval):
            if not save_get_items:
                self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(BATTLE_STATUS_A, screenshot=save_get_items, genre='status',
                                  interval=self.battle_status_click_interval):
            logger.warning('Battle status: A')
            if not save_get_items:
                self.device.sleep((0.25, 0.5))
            return True

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
            return True
        if self.appear_then_click(GET_ITEMS_2, screenshot=save_get_items, genre='get_items', offset=5,
                                  interval=self.battle_status_click_interval):
            self.interval_reset(BATTLE_STATUS_S)
            self.interval_reset(BATTLE_STATUS_A)
            return True

        return False

    def handle_exp_info(self):
        """
        Returns:
            bool:
        """
        if self.appear_then_click(EXP_INFO_S):
            self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(EXP_INFO_A):
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
            return True

        return False

    def combat_status(self, save_get_items=False, expected_end=None):
        """
        Args:
            save_get_items (bool):
            expected_end (str): with_searching, no_searching, in_stage.
        """
        logger.info('Combat status')
        logger.attr('expected_end', expected_end)
        while 1:
            self.device.screenshot()

            # Combat status
            if self.handle_get_ship(save_get_items=save_get_items):
                continue
            if self.handle_get_items(save_get_items=save_get_items):
                continue
            if self.handle_battle_status(save_get_items=save_get_items):
                continue
            if self.handle_popup_confirm():
                continue
            if self.handle_exp_info():
                continue
            if self.handle_urgent_commission(save_get_items=save_get_items):
                continue
            if self.handle_story_skip():
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

    def combat(self, balance_hp=None, emotion_reduce=None, func=None, call_submarine_at_boss=None, save_get_items=None,
               expected_end=None, fleet_index=1):
        """
        Execute a combat.
        """
        balance_hp = balance_hp if balance_hp is not None else self.config.ENABLE_HP_BALANCE
        emotion_reduce = emotion_reduce if emotion_reduce is not None else self.config.ENABLE_EMOTION_REDUCE
        auto = self.config.COMBAT_AUTO_MODE == 'combat_auto'
        call_submarine_at_boss = call_submarine_at_boss if call_submarine_at_boss is not None else self.config.SUBMARINE_CALL_AT_BOSS
        save_get_items = save_get_items if save_get_items is not None else self.config.ENABLE_SAVE_GET_ITEMS
        self.battle_status_click_interval = 3 if save_get_items else 0

        # if not hasattr(self, 'emotion'):
        #     self.emotion = Emotion(config=self.config)

        self.combat_preparation(
            balance_hp=balance_hp, emotion_reduce=emotion_reduce, auto=auto, fleet_index=fleet_index)
        self.combat_execute(
            auto=auto, call_submarine_at_boss=call_submarine_at_boss, save_get_items=save_get_items)
        self.combat_status(
            save_get_items=save_get_items, expected_end=expected_end)
        self.handle_map_after_combat_story()
