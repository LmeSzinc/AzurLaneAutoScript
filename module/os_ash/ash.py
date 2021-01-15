from module.combat.combat import Combat, BATTLE_PREPARATION
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from module.os_ash.assets import *
from module.ui.page import page_os
from module.ui.switch import Switch
from module.ui.ui import UI

OCR_BEACON_REMAIN = DigitCounter(BEACON_REMAIN, threshold=256, name='OCR_ASH_REMAIN')
OCR_BEACON_TIER = Digit(BEACON_TIER, name='OCR_ASH_TIER')

SWITCH_BEACON = Switch(name='Beacon', offset=(20, 20))
SWITCH_BEACON.add_status('mine', BEACON_LIST)
SWITCH_BEACON.add_status('list', BEACON_MY)

RECORD_OPTION = ('DailyRecord', 'ash')
RECORD_SINCE = (0,)


class AshCombat(Combat):
    def handle_battle_status(self, save_get_items=False):
        """
        Args:
            save_get_items (bool):

        Returns:
            bool:
        """
        if self.is_combat_executing():
            return False
        if self.appear_then_click(BATTLE_STATUS, screenshot=save_get_items, genre='status',
                                  interval=self.battle_status_click_interval):
            if not save_get_items:
                self.device.sleep((0.25, 0.5))
            return True

        return False

    def combat(self, balance_hp=False, emotion_reduce=False, auto_mode='combat_auto', call_submarine_at_boss=False,
               save_get_items=False, expected_end=None, fleet_index=1):
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

        self.combat_preparation(
            balance_hp=balance_hp, emotion_reduce=emotion_reduce, auto=auto_mode, fleet_index=fleet_index)
        self.combat_execute(
            auto=auto_mode, call_submarine_at_boss=call_submarine_at_boss, save_get_items=save_get_items)
        self.combat_status(
            save_get_items=save_get_items, expected_end=expected_end)
        # self.handle_map_after_combat_story()

        logger.info('Combat end.')


class OSAsh(AshCombat, UI):
    def is_in_ash(self):
        return self.appear(ASH_CHECK, offset=(20, 20))

    def ash_beacon_select(self, tier=15, trial=5):
        """
        Args:
            tier (int): Try to find a beacon with tier greater or equal argument tier.
            trial (int): If not found after several trial, attack current one.

        Returns:
            bool: If selected beacon satisfies input tier.

        Page:
            in: ASH_CHECK, beacon list
        """
        # Ensure BEACON_TIER shown up
        # When entering beacon list, tier number wasn't shown immediately.
        for n in range(10):
            if self.image_color_count(BEACON_TIER, color=(0, 0, 0), threshold=221, count=50):
                break

            self.device.screenshot()
            if n >= 9:
                logger.warning('Waiting for beacon tier timeout')

        # Select beacon
        for _ in range(trial):
            current = OCR_BEACON_TIER.ocr(self.device.image)
            if current == tier:
                return True
            else:
                self.device.click(BEACON_NEXT)
                self.device.sleep((0.3, 0.5))
                self.device.screenshot()

        logger.info(f'Tier {tier} beacon not found after {trial} trial, use current beacon')
        return False

    def ash_beacon_assist(self):
        """
        Run beacon ash assist.

        Pages:
            in: Any page
            out: page_os
        """
        self.ui_ensure(page_os)
        self.ui_click(ASH_ENTRANCE, check_button=self.is_in_ash, skip_first_screenshot=True)
        SWITCH_BEACON.set('list', main=self)

        for _ in range(4):
            remain, _, _ = OCR_BEACON_REMAIN.ocr(self.device.image)
            if remain <= 0:
                logger.info('Ash beacon exhausted')
                break

            self.ash_beacon_select(tier=self.config.OS_ASH_ASSIST_TIER)
            self.ui_click(ASH_START, check_button=BATTLE_PREPARATION, skip_first_screenshot=True)
            self.combat(expected_end=self.is_in_ash)
            continue

        self.device.sleep((0.5, 0.8))
        self.device.screenshot()
        self.ui_click(ASH_QUIT, check_button=ASH_ENTRANCE, skip_first_screenshot=True)
        return True


class AshDaily(OSAsh):
    def record_executed_since(self):
        return self.config.record_executed_since(option=RECORD_OPTION, since=RECORD_SINCE)

    def record_save(self):
        return self.config.record_save(option=RECORD_OPTION)

    def run(self):
        return self.ash_beacon_assist()
