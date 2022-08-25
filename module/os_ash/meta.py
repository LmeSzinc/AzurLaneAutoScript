from enum import Enum

from module.logger import logger
from module.ocr.ocr import DigitCounter, Digit
from module.os_ash.ash import AshCombat
from module.os_ash.assets import *
from module.os_handler.map_event import MapEventHandler
from module.ui.page import page_reward
from module.ui.ui import UI


class MetaState(Enum):
    INIT = 'no meta begin'
    ATTACKING = 'a meta under attack'
    COMPLETE = 'reward to be collected'


OCR_BEACON_TIER = Digit(BEACON_TIER, name='OCR_ASH_TIER')
OCR_META_DAMAGE = Digit(META_DAMAGE, name='OCR_META_DAMAGE')


class Meta(UI, MapEventHandler):

    def digit_ocr_point_and_check(self, button: Button, check_number: int):
        point_ocr = DigitCounter(button, letter=(235, 235, 235), threshold=160, name='POINT_OCR')
        point, _, _ = point_ocr.ocr(self.device.image)
        if point >= check_number:
            return True
        return False

    def handle_map_event(self, drop=None):
        if super().handle_map_event(drop):
            return True
        if self.appear_then_click(META_AUTO_CONFIRM, offset=(20, 20), interval=2):
            return True


class OpsiAshBeacon(Meta):
    PAGE_MAIN_BEACON_PERCENT = Button(area=(850, 22, 940, 46), button=(280, 180, 560, 510), color=(0, 0, 0))
    PAGE_MAIN_DOSSIER_PERCENT = Button(area=(1050, 22, 1160, 46), button=(720, 180, 990, 510), color=(0, 0, 0))
    PAGE_BEACON_POINT_PERCENT = Button(area=(720, 25, 820, 50), button=(560, 260, 730, 440), color=(0, 0, 0))
    PAGE_DOSSIER_POINT_PERCENT = Button(area=(980, 25, 1090, 50), button=(560, 260, 730, 440), color=(0, 0, 0))

    def _attack_meta(self):
        combat = AshCombat(config=self.config, device=self.device)
        while 1:
            self.device.screenshot()

            if self.handle_map_event():
                continue
            state = self._get_state()
            if MetaState.INIT == state:
                if self._begin_meta():
                    continue
                else:
                    # Normal finish
                    return True
            if MetaState.ATTACKING == state:
                self._pre_attack()
                if self._satisfy_attack_condition():
                    combat.combat(expected_end=self._in_self_meta_page, save_get_items=False, emotion_reduce=False)
                    continue
                else:
                    # Delay finish
                    return False
            if MetaState.COMPLETE == state:
                self.appear_then_click(BEACON_REWARD, offset=(30, 30), interval=2)
                continue

    def _satisfy_attack_condition(self):
        # Page dossier
        if self.appear(DOSSIER_LIST, offset=(20, 20)):
            return True
        if self.appear(BEACON_LIST, offset=(20, 20)):
            if self.config.OpsiAshBeacon_OneHitMode:
                damage = OCR_META_DAMAGE.ocr(self.device.image)
                if damage <= 0:
                    logger.info('This meta has been attacked! Damage is ' + str(damage))
                    return True
        return False

    def _pre_attack(self):
        # Page beacon or dossier
        if self.appear(BEACON_LIST, offset=(20, 20)) \
                or self.appear(DOSSIER_LIST, offset=(20, 20)):
            if self.config.OpsiAshBeacon_OneHitMode or self.config.OpsiAshBeacon_RequestAssist:
                self._ask_for_help()

    def _ask_for_help(self):
        """
        Request help from friends, guild and world.

        Pages:
            in: is_in_ash
            out: is_in_ash
        """
        self.ui_click(click_button=HELP_ENTER, check_button=HELP_CONFIRM)
        # Here use simple clicks. Dropping some clicks is acceptable, no need to confirm they are selected.
        self.appear_then_click(HELP_1, offset=(100, 20), interval=2)
        self.device.sleep((0.1, 0.3))
        self.appear_then_click(HELP_2, offset=(100, 20), interval=2)
        self.device.sleep((0.1, 0.3))
        self.appear_then_click(HELP_3, offset=(100, 20), interval=2)
        self.ui_click(click_button=HELP_CONFIRM, check_button=HELP_ENTER)

    def _begin_meta(self):
        # Page meta main
        if self.appear(ASH_SHOWDOWN, offset=(30, 30)):
            if self.config.OpsiAshBeacon_AshAttack \
                    and self.digit_ocr_point_and_check(self.PAGE_MAIN_BEACON_PERCENT, 100):
                self.device.click(self.PAGE_MAIN_BEACON_PERCENT)
                return True
            if self.config.OpsiDossierBeacon_Enable \
                    and self.digit_ocr_point_and_check(self.PAGE_MAIN_DOSSIER_PERCENT, 100):
                self.device.click(self.PAGE_MAIN_DOSSIER_PERCENT)
                return True
            return False
        # Page beacon
        if self.appear(BEACON_LIST, offset=(20, 20)):
            if self.config.OpsiAshBeacon_AshAttack \
                    and self.digit_ocr_point_and_check(self.PAGE_BEACON_POINT_PERCENT, 100):
                self.device.click(self.PAGE_BEACON_POINT_PERCENT)
                return True
        # Page dossier
        if self.appear(DOSSIER_LIST, offset=(20, 20)):
            if self.config.OpsiDossierBeacon_Enable \
                    and self.digit_ocr_point_and_check(self.PAGE_DOSSIER_POINT_PERCENT, 100):
                self.device.click(self.PAGE_DOSSIER_POINT_PERCENT)
                return True
        self.appear_then_click(ASH_QUIT, offset=(10, 10), interval=2)
        return True

    def _get_state(self):
        # Page beacon or dossier
        if self.appear(BEACON_LIST, offset=(20, 20)) \
                or self.appear(DOSSIER_LIST, offset=(20, 20)):
            if self.appear(ASH_START, offset=(20, 20)):
                return MetaState.ATTACKING
            if self.appear(BEACON_REWARD, offset=(20, 20)):
                return MetaState.COMPLETE
        return MetaState.INIT

    def _in_self_meta_page(self):
        return self.appear(ASH_SHOWDOWN, offset=(30, 30)) \
               or self.appear(BEACON_LIST, offset=(20, 20)) \
               or self.appear(DOSSIER_LIST, offset=(20, 20))

    def _ensure_self_meta_page(self):
        while 1:
            self.device.screenshot()

            if self._in_self_meta_page():
                return True
            if self.handle_map_event():
                continue
            if self.appear_then_click(META_ENTRANCE, offset=(10, 10), interval=2):
                continue

    def _begin_beacon(self):
        self._ensure_self_meta_page()
        return self._attack_meta()

    def run(self):
        self.ui_ensure(page_reward)
        if self._begin_beacon():
            self.config.task_delay(server_update=True)
        else:
            self.config.task_delay(minute=30)


class AshBeaconAssist(Meta):

    def _attack_meta(self):
        combat = AshCombat(config=self.config, device=self.device)
        while 1:
            self.device.screenshot()

            if self.handle_map_event():
                continue
            if self._satisfy_attack_condition():
                self._ensure_meta_level()
                combat.combat(expected_end=self._in_their_meta_page, save_get_items=False, emotion_reduce=False)
                continue
            else:
                break

    def _satisfy_attack_condition(self):
        return self.digit_ocr_point_and_check(BEACON_REMAIN, 1)

    def _ensure_meta_level(self):
        """
        Select an meta whose level satisfies
        """
        # Ensure BEACON_TIER shown up
        # When entering beacon list, tier number wasn't shown immediately.
        tier = self.config.OpsiAshAssist_Tier
        for n in range(10):
            if self.image_color_count(BEACON_TIER, color=(0, 0, 0), threshold=221, count=50):
                break

            self.device.screenshot()
            if n >= 9:
                logger.warning('Waiting for beacon tier timeout')
        # Select beacon
        flag = False
        for _ in range(5):
            current = OCR_BEACON_TIER.ocr(self.device.image)
            if current >= tier:
                flag = True
                break
            else:
                self.device.click(BEACON_NEXT)
                self.device.sleep((0.3, 0.5))
                self.device.screenshot()
        if not flag:
            logger.info(f'Tier {tier} beacon not found after 5 trial, use current beacon')

    def _in_their_meta_page(self):
        return self.appear(BEACON_MY, offset=(20, 20))

    def _ensure_their_meta_page(self):
        while 1:
            self.device.screenshot()

            if self._in_their_meta_page():
                return True
            if self.handle_map_event():
                continue
            if self.appear_then_click(META_ENTRANCE, offset=(10, 10), interval=2):
                continue
            if self.appear_then_click(ASH_SHOWDOWN, offset=(20, 20), interval=2):
                continue
            if self.appear_then_click(BEACON_LIST, offset=(200, 20), interval=2):
                continue
            if self.appear_then_click(DOSSIER_LIST, offset=(20, 20), interval=2):
                continue

    def _begin_meta_assist(self):
        self._ensure_their_meta_page()
        return self._attack_meta()

    def run(self):
        self.ui_ensure(page_reward)
        self._begin_meta_assist()
        self.config.task_delay(server_update=True)
