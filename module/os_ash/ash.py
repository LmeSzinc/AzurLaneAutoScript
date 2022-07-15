from module.base.timer import Timer
from module.base.utils import color_bar_percentage, image_left_strip
from module.combat.combat import BATTLE_PREPARATION, GET_ITEMS_1, Combat
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from module.os.assets import MAP_GOTO_GLOBE, GLOBE_GOTO_MAP
from module.os_ash.assets import *
from module.os_handler.assets import IN_MAP
from module.os_handler.map_event import MapEventHandler
from module.ui.assets import BACK_ARROW
from module.ui.page import page_os
from module.ui.switch import Switch
from module.ui.ui import UI


class DailyDigitCounter(DigitCounter):
    def pre_process(self, image):
        image = super().pre_process(image)
        image = image_left_strip(image, threshold=120, length=35)
        return image


OCR_BEACON_REMAIN = DigitCounter(BEACON_REMAIN, threshold=256, name='OCR_ASH_REMAIN')
OCR_BEACON_TIER = Digit(BEACON_TIER, name='OCR_ASH_TIER')

SWITCH_BEACON = Switch(name='Beacon', offset=(20, 20))
SWITCH_BEACON.add_status('mine', BEACON_LIST)
SWITCH_BEACON.add_status('list', BEACON_MY)


class AshBeaconFinished(Exception):
    pass


class AshCombat(Combat):
    def handle_battle_status(self, drop=None):
        """
        Args:
            drop (DropImage):

        Returns:
            bool:
        """
        if self.is_combat_executing():
            return False
        if super().handle_battle_status(drop=drop):
            return True
        if self.appear(BATTLE_STATUS, offset=(20, 20), interval=self.battle_status_click_interval):
            if drop:
                drop.handle_add(self)
            else:
                self.device.sleep((0.25, 0.5))
            self.device.click(BATTLE_STATUS)
            return True
        if self.appear(BATTLE_PREPARATION, offset=(30, 30), interval=3):
            self.device.click(BACK_ARROW)
            return True

        return False

    def handle_battle_preparation(self):
        if super().handle_battle_preparation():
            return True

        if self.appear_then_click(ASH_START, offset=(30, 30)):
            return True
        if self.handle_get_items():
            return True
        if self.appear(BEACON_REWARD):
            logger.info("Ash beacon already finished.")
            raise AshBeaconFinished
        if self.appear(BEACON_EMPTY, offset=(20, 20)):
            logger.info("Ash beacon already empty.")
            raise AshBeaconFinished

        return False

    def combat(self, *args, **kwargs):
        try:
            super().combat(*args, **kwargs)
        except AshBeaconFinished:
            pass


class OSAsh(UI, MapEventHandler):
    ash_entrance_offset = (200, 5)
    beacon_entrance_offset = (100, 100)

    def is_in_ash(self):
        return self.appear(ASH_CHECK, offset=(100, 20))

    def is_in_map(self):
        return self.appear(IN_MAP, offset=(200, 5))

    def _ash_assist_enter_from_map(self, offset=(200, 5), skip_first_screenshot=True):
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

            if self.appear_then_click(MAP_GOTO_GLOBE, offset=offset, interval=5):
                confirm_timer.reset()
                continue
            if self.appear_then_click(ASH_SHOWDOWN, offset=(30, 30), interval=5):
                confirm_timer.reset()
                continue
            if self.appear_then_click(ASH_ENTRANCE, offset=offset, interval=5):
                confirm_timer.reset()
                continue
            if self._handle_ash_beacon_reward():
                confirm_timer.reset()
                continue
            if self.handle_popup_confirm('GOTO_GLOBE'):
                # Popup: Leaving current zone will terminate meowfficer searching
                confirm_timer.reset()
                continue
            if self.handle_map_event():
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
            if current >= tier:
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
        self.ui_ensure(page_os)
        self._ash_assist_enter_from_map(offset=self.ash_entrance_offset, skip_first_screenshot=True)

        for _ in range(10):
            SWITCH_BEACON.set('list', main=self)
            remain, _, _ = OCR_BEACON_REMAIN.ocr(self.device.image)
            if remain <= 0:
                logger.info('Ash beacon exhausted')
                break

            self._ash_beacon_select(tier=self.config.OpsiAshAssist_Tier)
            ash_combat.combat(expected_end=self.is_in_ash, save_get_items=False, emotion_reduce=False)

        self.device.sleep((0.5, 0.8))
        self.device.screenshot()
        self._ash_exit_to_globe()
        return True

    _ash_fully_collected = False

    def ash_collect_status(self):
        """
        Returns:
            int: 0 to 100.
        """
        if self._ash_fully_collected:
            return 0
        if self.image_color_count(ASH_COLLECT_STATUS, color=(235, 235, 235), threshold=221, count=20):
            logger.info('Ash beacon status: light')
            ocr_collect = DigitCounter(
                ASH_COLLECT_STATUS, letter=(235, 235, 235), threshold=160, name='OCR_ASH_COLLECT_STATUS')
            ocr_daily = DailyDigitCounter(
                ASH_DAILY_STATUS, letter=(235, 235, 235), threshold=160, name='OCR_ASH_DAILY_STATUS')
        elif self.image_color_count(ASH_COLLECT_STATUS, color=(140, 142, 140), threshold=221, count=20):
            logger.info('Ash beacon status: gray')
            ocr_collect = DigitCounter(
                ASH_COLLECT_STATUS, letter=(140, 142, 140), threshold=160, name='OCR_ASH_COLLECT_STATUS')
            ocr_daily = DailyDigitCounter(
                ASH_DAILY_STATUS, letter=(140, 142, 140), threshold=160, name='OCR_ASH_DAILY_STATUS')
        else:
            # If OS daily mission received or finished, the popup will cover beacon status.
            logger.info('Ash beacon status is covered, will check next time')
            return 0

        status, _, _ = ocr_collect.ocr(self.device.image)
        daily, _, _ = ocr_daily.ocr(self.device.image)

        if daily >= 200:
            logger.info('Ash beacon fully collected today')
            self._ash_fully_collected = True

        if status < 0:
            status = 0
        return status

    def _ash_mine_enter_from_map(self, skip_first_screenshot=True):
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
            if self.appear_then_click(ASH_SHOWDOWN, offset=(30, 30), interval=3):
                continue
            if self.appear_then_click(BEACON_ENTER, offset=self.beacon_entrance_offset, interval=2):
                continue
            if self._handle_ash_beacon_reward():
                continue
            if self.handle_map_event():
                # Random map events, may slow to show.
                continue

            # End:
            if self.appear(ASH_START, offset=(30, 30)):
                break

    def _ash_exit_to_map(self, skip_first_screenshot=True):
        """
        Pages:
            in: is_in_ash
            out: is_in_map
        """
        click_timer = Timer(3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_map():
                break

            if click_timer.reached() and self.is_in_ash():
                self.device.click(ASH_QUIT)
                click_timer.reset()
                continue
            if self.appear(ASH_SHOWDOWN, offset=(30, 30), interval=3):
                self.device.click(ASH_QUIT)
                continue
            if self.appear_then_click(GLOBE_GOTO_MAP, offset=(20, 20), interval=3):
                continue
            if self.handle_map_event():
                continue

    def _ash_exit_to_globe(self, skip_first_screenshot=True):
        """
        Pages:
            in: is_in_ash
            out: is_in_map
        """
        click_timer = Timer(3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(ASH_ENTRANCE, offset=self.ash_entrance_offset):
                break

            if click_timer.reached() and self.is_in_ash():
                self.device.click(ASH_QUIT)
                click_timer.reset()
                continue
            if self.appear(ASH_SHOWDOWN, offset=(30, 30), interval=3):
                self.device.click(ASH_QUIT)
                continue
            if self.appear_then_click(MAP_GOTO_GLOBE, offset=(20, 20), interval=3):
                continue
            if self.handle_map_event():
                continue

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
            elif self.appear(BEACON_ENTER, offset=self.beacon_entrance_offset):
                # If previous beacon is not completed, the previous beacon is attacked in this round.
                # Then found a new beacon, after attack.
                if confirm_timer.reached():
                    logger.info('Ash beacon attack finished, but found another beacon')
                    return False
            else:
                confirm_timer.reset()

            # Accident clicks
            if self.appear(BATTLE_PREPARATION, offset=(30, 30), interval=2):
                self.device.click(BACK_ARROW)
                continue
            if self.appear(HELP_CONFIRM, offset=(30, 30), interval=2):
                self.device.click(BACK_ARROW)
                continue
            # Redirected by game
            if self.appear_then_click(ASH_SHOWDOWN, offset=(30, 30), interval=2):
                continue
            # Combat and rewards
            if self._handle_ash_beacon_reward():
                continue
            if self.appear(ASH_START, offset=(30, 30)):
                ash_combat.combat(expected_end=self.is_in_ash, save_get_items=False, emotion_reduce=False)
                continue

    def handle_ash_beacon_attack(self):
        """
        Returns:
            bool: If attacked.

        Pages:
            in: is_in_map
            out: is_in_map
        """
        if not self.config.OpsiAshBeacon_AshAttack:
            return False
        if self.ash_collect_status() < 100:
            return False

        for _ in range(3):
            self._ash_mine_enter_from_map()
            if self.config.OpsiAshBeacon_RequestAssist:
                self._ash_help()
            finish = self._ash_beacon_attack()
            if finish:
                break

        self._ash_exit_to_map()
        return True


class AshBeaconAssist(OSAsh):
    def run(self):
        """
        Run daily ash beacon assist.

        Pages:
            in: Any page
            out: page_os
        """
        self.ash_beacon_assist()
        self.config.task_delay(server_update=True)
