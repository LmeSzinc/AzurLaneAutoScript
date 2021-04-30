from module.base.timer import Timer
from module.base.utils import color_bar_percentage
from module.combat.combat import Combat, BATTLE_PREPARATION, GET_ITEMS_1
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from module.os.assets import MAP_GOTO_GLOBE
from module.os_ash.assets import *
from module.os_handler.assets import IN_MAP
from module.ui.assets import BACK_ARROW
from module.ui.page import page_os
from module.ui.switch import Switch
from module.ui.ui import UI

OCR_BEACON_REMAIN = DigitCounter(BEACON_REMAIN, threshold=256, name='OCR_ASH_REMAIN')
OCR_BEACON_TIER = Digit(BEACON_TIER, name='OCR_ASH_TIER')
OCR_ASH_COLLECT_STATUS = DigitCounter(
    ASH_COLLECT_STATUS, letter=(235, 235, 235), threshold=160, name='OCR_ASH_COLLECT_STATUS')

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
        if self.appear_then_click(BATTLE_STATUS, offset=(20, 20),
                                  screenshot=save_get_items, genre='status', interval=3):
            if not save_get_items:
                self.device.sleep((0.25, 0.5))
            return True
        if self.appear(BATTLE_PREPARATION, offset=(30, 30), interval=3):
            self.device.click(BACK_ARROW)
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


class OSAsh(UI):
    def is_in_ash(self):
        return self.appear(ASH_CHECK, offset=(20, 20))

    def is_in_map(self):
        return self.appear(IN_MAP, offset=(200, 5))

    def _ash_beacon_enter_from_map(self, offset=(200, 5), skip_first_screenshot=True):
        """
        Args:
            offset:
            skip_first_screenshot:

        Pages:
            in: IN_MAP
            out: is_in_ash
        """
        confirm_timer = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(MAP_GOTO_GLOBE, offset=offset, interval=3):
                confirm_timer.reset()
                continue
            if self.appear_then_click(ASH_ENTRANCE, offset=offset, interval=3):
                confirm_timer.reset()
                continue
            if self._handle_ash_beacon_reward():
                confirm_timer.reset()
                continue
            if self.handle_popup_confirm('GOTO_GLOBE'):
                # Popup: Leaving current zone will terminate meowfficer searching
                confirm_timer.reset()
                continue

            # End
            if self.is_in_ash():
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

    def _ash_beacon_select(self, tier=15, trial=5):
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
        # If the main story in OS is not cleared, ASH_ENTRANCE is the first button counted from bottom right.
        # When main story is cleared, ASH_ENTRANCE move to the second one.
        # Here use an offset to handle that.
        ash_combat = AshCombat(self.config, self.device)
        entrance_offset = (200, 5)
        self.ui_ensure(page_os)
        self._ash_beacon_enter_from_map(offset=entrance_offset, skip_first_screenshot=True)

        for _ in range(4):
            SWITCH_BEACON.set('list', main=self)
            remain, _, _ = OCR_BEACON_REMAIN.ocr(self.device.image)
            if remain <= 0:
                logger.info('Ash beacon exhausted')
                break

            self._ash_beacon_select(tier=self.config.OS_ASH_ASSIST_TIER)
            self.ui_click(ASH_START, check_button=BATTLE_PREPARATION, offset=(30, 30),
                          additional=ash_combat.handle_combat_automation_confirm, skip_first_screenshot=True)
            ash_combat.combat(expected_end=self.is_in_ash)
            continue

        self.device.sleep((0.5, 0.8))
        self.device.screenshot()
        self.ui_click(ASH_QUIT, check_button=ASH_ENTRANCE, offset=entrance_offset, skip_first_screenshot=True)
        return True

    _ash_fully_collected = False

    def ash_collect_status(self):
        """
        Returns:
            int: 0 to 100.
        """
        if self._ash_fully_collected:
            return 0
        if not self.image_color_count(ASH_COLLECT_STATUS, color=(235, 235, 235), threshold=221, count=20):
            if self.image_color_count(ASH_COLLECT_STATUS, color=(82, 85, 82), threshold=235, count=50):
                logger.info('Ash beacon fully collected today')
                self._ash_fully_collected = True
                return 0
            else:
                # If OS daily mission received or finished, the popup will cover beacon status.
                logger.info('Ash beacon status is covered, will check next time')
                return 0

        status, _, _ = OCR_ASH_COLLECT_STATUS.ocr(self.device.image)
        if status < 0:
            status = 0
        if status > 100:
            status = 100
        return status

    def _ash_enter_from_map(self, skip_first_screenshot=True):
        """
        Pages:
            in: is_in_map
            out: is_in_ash
        """
        in_map_timeout = Timer(2, count=3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if in_map_timeout.reached() and self.is_in_map():
                self.device.click(ASH_COLLECT_STATUS)
                in_map_timeout.reset()
                continue
            if self.appear_then_click(ASH_ENTER_CONFIRM, offset=(30, 50), interval=2):
                continue
            if self.appear_then_click(BEACON_ENTER, offset=(20, 20), interval=2):
                continue
            if self._handle_ash_beacon_reward():
                continue

            # End:
            if self.appear(ASH_START, offset=(30, 30)):
                break

    def _ash_help(self):
        """
        Request help from friends, guild and world.

        Pages:
            in: is_in_ash
            out: is_in_ash
        """
        self.ui_click(click_button=HELP_ENTER, check_button=HELP_CONFIRM)
        # Here use simple clicks. Dropping some clicks is acceptable, no need to confirm they are selected.
        self.device.click(HELP_1)
        self.device.sleep((0.1, 0.3))
        self.device.click(HELP_2)
        self.device.sleep((0.1, 0.3))
        self.device.click(HELP_3)
        self.ui_click(click_button=HELP_CONFIRM, check_button=HELP_ENTER)

    def _handle_ash_beacon_reward(self):
        """
        Returns:
            bool: If clicked
        """
        if self.appear_then_click(BEACON_REWARD, interval=2):
            return True
        if self.appear(GET_ITEMS_1, interval=2):
            self.device.click(BEACON_REWARD)
            return True

        return False

    def _ash_beacon_attack(self):
        """
        Attack ash beacon until it's killed.

        Returns:
            bool: If all beacon finished

        Pages:
            in: is_in_ash
            out: is_in_ash
        """
        logger.info('Ash beacon attack')
        confirm_timer = Timer(1, count=2).start()
        ash_combat = AshCombat(self.config, self.device)

        while 1:
            self.device.screenshot()
            percent = color_bar_percentage(
                self.device.image, BEACON_HP_PERCENTAGE.area, prev_color=(181, 56, 57), threshold=15)
            logger.attr('Ash_beacon_hp', f'{int(percent * 100)}%')

            # End
            if self.appear(BEACON_EMPTY, offset=(20, 20)):
                if confirm_timer.reached():
                    logger.info('Ash beacon attack finished')
                    return True
            elif self.appear(BEACON_ENTER, offset=(20, 20)):
                # If previous beacon is not completed, the previous beacon is attacked in this round.
                # Then found a new beacon, after attack.
                if confirm_timer.reached():
                    logger.info('Ash beacon attack finished, but found another beacon')
                    return False
            else:
                confirm_timer.reset()

            if self._handle_ash_beacon_reward():
                continue
            if self.appear(ASH_START, offset=(30, 30)):
                self.ui_click(ASH_START, check_button=BATTLE_PREPARATION, offset=(30, 30),
                              additional=ash_combat.handle_combat_automation_confirm, skip_first_screenshot=True)
                ash_combat.combat(expected_end=self.is_in_ash)
                continue

    def handle_ash_beacon_attack(self):
        """
        Returns:
            bool: If attacked.

        Pages:
            in: is_in_map
            out: is_in_map
        """
        if not self.config.ENABLE_OS_ASH_ATTACK:
            return False
        if self.ash_collect_status() < 100:
            return False

        for _ in range(3):
            self._ash_enter_from_map()
            self._ash_help()
            finish = self._ash_beacon_attack()
            if finish:
                break

        self.ui_click(ASH_QUIT, check_button=self.is_in_map, skip_first_screenshot=True)
        return True


class AshDaily(OSAsh):
    def record_executed_since(self):
        return self.config.record_executed_since(option=RECORD_OPTION, since=RECORD_SINCE)

    def record_save(self):
        return self.config.record_save(option=RECORD_OPTION)

    def run(self):
        return self.ash_beacon_assist()
