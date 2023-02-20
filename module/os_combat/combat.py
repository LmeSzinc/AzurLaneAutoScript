from module.combat.assets import *
from module.combat.combat import Combat as Combat_
from module.logger import logger
from module.os_combat.assets import *
from module.os_handler.assets import *
from module.os_handler.map_event import MapEventHandler
from module.base.timer import Timer


class ContinuousCombat(Exception):
    pass


class Combat(Combat_, MapEventHandler):
    def combat_appear(self):
        """
        Returns:
            bool: If enter combat.
        """
        if not self.is_in_map():
            if self.is_combat_loading():
                return True

        if self.appear(BATTLE_PREPARATION):
            return True
        if self.appear(SIREN_PREPARATION, offset=(20, 20)):
            return True
        if self.appear(BATTLE_PREPARATION_WITH_OVERLAY) and self.handle_combat_automation_confirm():
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

        # if emotion_reduce:
        #     self.emotion.wait(fleet=fleet_index)
        # if balance_hp:
        #     self.hp_balance()

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
            # if self.handle_combat_low_emotion():
            #     continue
            # if balance_hp and self.handle_emergency_repair_use():
            #     continue
            if self.appear_then_click(BATTLE_PREPARATION, interval=2):
                continue
            if self.appear_then_click(SIREN_PREPARATION, offset=(20, 20), interval=2):
                continue
            if self.handle_popup_confirm('ENHANCED_ENEMY'):
                continue
            if self.handle_combat_automation_confirm():
                continue
            if self.handle_story_skip():
                continue

            # End
            if self.is_combat_executing():
                # if emotion_reduce:
                #     self.emotion.reduce(fleet_index)
                break

    def handle_exp_info(self):
        if self.is_combat_executing():
            return False
        if self.__os_combat_drop:
            sleep = (1.5, 2)
        else:
            sleep = (0.25, 0.5)
        if self.appear_then_click(EXP_INFO_S):
            self.device.sleep(sleep)
            return True
        if self.appear_then_click(EXP_INFO_A):
            self.device.sleep(sleep)
            return True
        if self.appear_then_click(EXP_INFO_B):
            self.device.sleep(sleep)
            return True
        if self.appear_then_click(EXP_INFO_C):
            self.device.sleep(sleep)
            return True
        if self.appear_then_click(EXP_INFO_D):
            self.device.sleep(sleep)
            return True

        return False

    def handle_get_items(self, drop=None):
        """
        Click CLICK_SAFE_AREA instead of button itself.

        Args:
            drop (DropImage):

        Returns:
            bool:
        """
        if self.appear(GET_ITEMS_1, offset=5, interval=self.battle_status_click_interval):
            if drop:
                drop.handle_add(self, before=2)
            self.device.click(CLICK_SAFE_AREA)
            self.interval_reset(BATTLE_STATUS_S)
            self.interval_reset(BATTLE_STATUS_A)
            self.interval_reset(BATTLE_STATUS_B)
            return True
        if self.appear(GET_ITEMS_2, offset=5, interval=self.battle_status_click_interval):
            if drop:
                drop.handle_add(self, before=2)
            self.device.click(CLICK_SAFE_AREA)
            self.interval_reset(BATTLE_STATUS_S)
            self.interval_reset(BATTLE_STATUS_A)
            self.interval_reset(BATTLE_STATUS_B)
            return True
        if self.appear(GET_ADAPTABILITY, offset=5, interval=self.battle_status_click_interval):
            if drop:
                drop.handle_add(self, before=2)
            self.device.click(CLICK_SAFE_AREA)
            self.interval_reset(BATTLE_STATUS_S)
            self.interval_reset(BATTLE_STATUS_A)
            self.interval_reset(BATTLE_STATUS_B)
            return True

        return False

    def _os_combat_expected_end(self):
        if self.handle_map_event(drop=self.__os_combat_drop):
            return False
        if self.combat_appear():
            raise ContinuousCombat

        return self.handle_os_in_map()

    __os_combat_drop = None

    def combat_status(self, drop=None, expected_end=None):
        self.__os_combat_drop = drop
        super().combat_status(drop=drop, expected_end=self._os_combat_expected_end)

    def combat(self, *args, save_get_items=False, **kwargs):
        """
        This handle continuous combat in operation siren.

        In siren scanning device, there are 2 ambush enemies with no interval.
        Fleet goto siren scanning device, attack one enemy, skip TB, attack another.
        Function `combat` has to confirm that combat was finished, and is_in_map.
        When handling siren scanning device, it will stuck in the second combat.
        This function inherits it and detect the second combat.
        """
        for count in range(3):
            if count >= 2:
                logger.warning('Too many continuous combat')

            try:
                super().combat(*args, save_get_items=save_get_items, **kwargs)
                break
            except ContinuousCombat:
                logger.info('Continuous combat detected')
                continue

    def handle_auto_search_battle_status(self, drop=None):
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

    def handle_auto_search_exp_info(self):
        if self.appear_then_click(EXP_INFO_C):
            self.device.sleep((0.25, 0.5))
            return True
        if self.appear_then_click(EXP_INFO_D):
            self.device.sleep((0.25, 0.5))
            return True

        return False

    def auto_search_combat(self, drop=None):
        """
        Args:
            drop (DropImage):

        Returns:
            bool: True if enemy cleared, False if fleet died.

        Pages:
            in: is_combat_loading()
            out: combat status
        """
        logger.info('Auto search combat loading')
        self.device.screenshot_interval_set('combat')
        while 1:
            self.device.screenshot()

            if self.handle_combat_automation_confirm():
                continue

            # End
            if self.handle_os_auto_search_map_option(drop=drop):
                break
            if self.is_combat_executing():
                break
            if self.is_in_map():
                break

        logger.info('Auto Search combat execute')
        self.submarine_call_reset()
        self.device.click_record_clear()
        self.combat_auto_reset()
        self.combat_manual_reset()
        submarine_mode = 'do_not_use'
        if self.config.Submarine_Fleet:
            submarine_mode = self.config.Submarine_Mode
        auto = 'combat_auto'
        if self.config.OpsiFleet_FleetMode:
            auto = self.config.OpsiFleet_FleetMode
        confirm_timer = Timer(10)
        confirm_timer.start()

        success = True
        while 1:
            self.device.screenshot()

            if self.handle_combat_auto(auto):
                continue
            if self.handle_combat_manual(auto):
                continue
            if self.handle_submarine_call(submarine_mode):
                continue
            # Don't change auto search option if failed
            enable = success if success is not None else None
            if self.handle_os_auto_search_map_option(drop=drop, enable=enable):
                continue

            # End
            if self.is_combat_executing():
                continue
            if self.handle_auto_search_battle_status():
                success = None
                continue
            if self.handle_auto_search_exp_info():
                success = None
                continue
            if self.handle_map_event():
                continue
            if self.is_in_map():
                self.device.screenshot_interval_set()
                break

        logger.info('Combat end.')
        return success
