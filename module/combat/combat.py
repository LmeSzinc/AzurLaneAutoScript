from module.base.timer import Timer
from module.base.utils import color_bar_percentage
from module.combat.assets import *
from module.combat.emotion import Emotion
from module.combat.hp_balancer import HPBalancer
from module.combat.submarine import SubmarineCall
from module.handler.enemy_searching import EnemySearchingHandler
from module.handler.urgent_commission import UrgentCommissionHandler
from module.logger import logger
from module.map.assets import MAP_OFFENSIVE
from module.map.exception import CampaignEnd
from module.retire.retirement import Retirement
from module.ui.assets import BACK_ARROW


class Combat(HPBalancer, UrgentCommissionHandler, EnemySearchingHandler, Retirement, SubmarineCall):
    _automation_set_timer = Timer(1)
    _emotion: Emotion

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
            if self.handle_retirement():
                self.map_offensive()
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
        return self.appear(PAUSE)

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
        # logger.info('start combat')

        while 1:
            self.device.screenshot()

            # Automation.
            if self.appear(BATTLE_PREPARATION):
                # if self.handle_combat_automation_confirm():
                #     continue
                if self.handle_combat_automation_set(auto=auto):
                    continue

            # Retirement
            if self.handle_retirement():
                continue

            # Combat start
            if self.appear_then_click(BATTLE_PREPARATION):
                continue

            if self.handle_combat_automation_confirm():
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

    def combat_execute(self, func=None, call_submarine_at_boss=False, save_get_items=False):
        """
        Args:
            func: Funtion to run when in combat.
            call_submarine_at_boss (bool):
            save_get_items (bool)
        """
        logger.info('Combat execute')
        self.submarine_call_reset()
        confirm_timer = Timer(10)
        confirm_timer.start()

        while 1:
            self.device.screenshot()

            if not confirm_timer.reached() and self.appear_then_click(AUTOMATION_CONFIRM, offset=True):
                continue

            if call_submarine_at_boss:
                pass
            else:
                if self.handle_submarine_call():
                    continue

            # End
            # if self.appear_then_click(BATTLE_STATUS):
            #     break
            if self.handle_battle_status(save_get_items=save_get_items):
                break

    def handle_battle_status(self, save_get_items=False):
        """
        Args:
            save_get_items (bool):

        Returns:
            bool:
        """
        if self.appear_then_click(BATTLE_STATUS_S, screenshot=save_get_items, genre='status'):
            self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(BATTLE_STATUS_A, screenshot=save_get_items, genre='status'):
            self.device.sleep((0.25, 0.5))
            logger.warning('Battle status: A')
            return True

        return False

    def handle_get_items(self, save_get_items=False):
        """
        Args:
            save_get_items (bool):

        Returns:
            bool:
        """
        if self.appear_then_click(GET_ITEMS_1, screenshot=save_get_items, genre='get_items', offset=5):
            return True
        if self.appear_then_click(GET_ITEMS_2, screenshot=save_get_items, genre='get_items', offset=5):
            return False

        return False

    def handle_get_ship(self):
        if self.appear_then_click(GET_SHIP):
            return True

        return False

    def combat_status(self, save_get_items=False, expected_end=None):
        """
        Args:
            save_get_items (bool):
            expected_end (str): with_searching, no_searching, in_stage.
        """
        logger.info('Combat status')
        while 1:
            self.device.screenshot()

            # Combat status
            if self.handle_get_items(save_get_items=save_get_items):
                continue
            if self.handle_battle_status(save_get_items=save_get_items):
                continue
            if self.handle_get_ship():
                continue
            if self.appear_then_click(EXP_INFO_S):
                self.device.sleep((0.25, 0.5))
                continue
            if self.appear_then_click(EXP_INFO_A):
                self.device.sleep((0.25, 0.5))
                continue
            if self.handle_urgent_commission(save_get_items=save_get_items):
                continue

            # End
            if expected_end is None:
                if self.handle_in_stage() or self.handle_in_map_with_enemy_searching():
                    break
            if isinstance(expected_end, str):
                if expected_end == 'in_stage' and self.handle_in_stage():
                    raise CampaignEnd('Boss clear')
                if expected_end == 'with_searching' and self.handle_in_map_with_enemy_searching():
                    break
                if expected_end == 'no_searching' and self.handle_in_map():
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
        auto = func is None
        call_submarine_at_boss = call_submarine_at_boss if call_submarine_at_boss is not None else self.config.SUBMARINE_CALL_AT_BOSS
        save_get_items = save_get_items if save_get_items is not None else self.config.ENABLE_SAVE_GET_ITEMS

        # if not hasattr(self, 'emotion'):
        #     self.emotion = Emotion(config=self.config)

        self.combat_preparation(
            balance_hp=balance_hp, emotion_reduce=emotion_reduce, auto=auto, fleet_index=fleet_index)
        self.combat_execute(
            func=func, call_submarine_at_boss=call_submarine_at_boss, save_get_items=save_get_items)
        self.combat_status(
            save_get_items=save_get_items, expected_end=expected_end)
