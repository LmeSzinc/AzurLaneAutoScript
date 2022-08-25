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


class MetaPage(Enum):
    ENTRANCE = 'meta entrance'
    BEACON = 'beacon page'
    DOSSIER = 'dossier page'
    BEACON_LIST = 'beacon list page'


OCR_BEACON_TIER = Digit(BEACON_TIER, name='OCR_ASH_TIER')
OCR_META_DAMAGE = Digit(META_DAMAGE, name='OCR_META_DAMAGE')


class MetaProcessor(UI):
    BEACON_PERCENT = Button(area=(850, 22, 940, 46), button=(280, 180, 560, 510), color=(0, 0, 0))
    DOSSIER_PERCENT = Button(area=(1050, 22, 1160, 46), button=(720, 180, 990, 510), color=(0, 0, 0))

    def support(self) -> bool:
        return self.appear(ASH_SHOWDOWN, offset=(30, 30))

    def page(self) -> MetaPage:
        return MetaPage.ENTRANCE

    def info(self):
        logger.info(self.page().name + '|' + self.get_state().name)

    def get_state(self) -> MetaState:
        return MetaState.INIT

    def begin_meta(self) -> bool:
        if self.config.OpsiAshBeacon_AshAttack and self.digit_ocr_point_and_check(self.BEACON_PERCENT, 100):
            self.device.click(self.BEACON_PERCENT)
            return True
        if self.config.OpsiDossierBeacon_Enable and self.digit_ocr_point_and_check(self.DOSSIER_PERCENT, 100):
            self.device.click(self.DOSSIER_PERCENT)
            return True
        return False

    def satisfy_attack_condition(self):
        return False

    def pre_attack(self):
        # Do nothing
        pass

    def digit_ocr_point_and_check(self, button: Button, check_number: int):
        point_ocr = DigitCounter(button, letter=(235, 235, 235), threshold=160, name='POINT_OCR')
        point, _, _ = point_ocr.ocr(self.device.image)
        if point >= check_number:
            return True
        return False


class MetaBeaconProcessor(MetaProcessor):
    POINT_PERCENT = Button(area=(720, 25, 820, 50), button=(560, 260, 730, 440), color=(0, 0, 0))

    def support(self) -> bool:
        return self.appear(BEACON_LIST, offset=(20, 20))

    def page(self) -> MetaPage:
        return MetaPage.BEACON

    def get_state(self) -> MetaState:
        if self.appear(ASH_START, offset=(20, 20)):
            return MetaState.ATTACKING
        if self.appear(BEACON_REWARD, offset=(20, 20)):
            return MetaState.COMPLETE
        return MetaState.INIT

    def begin_meta(self) -> bool:
        if self.config.OpsiAshBeacon_AshAttack and self.digit_ocr_point_and_check(self.POINT_PERCENT, 100):
            self.device.click(self.POINT_PERCENT)
        else:
            self.appear_then_click(ASH_QUIT, offset=(10, 10), interval=2)
        return True

    def satisfy_attack_condition(self):
        if self.config.OpsiAshBeacon_OneHitMode:
            damage = OCR_META_DAMAGE.ocr(self.device.image)
            if damage > 0:
                logger.info('This meta has been attacked! Damage is ' + str(damage))
                return False
        return True

    def pre_attack(self):
        if self.config.OpsiAshBeacon_OneHitMode or self.config.OpsiAshBeacon_RequestAssist:
            self.ask_for_help()

    def ask_for_help(self):
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


class MetaDossierProcessor(MetaBeaconProcessor):
    POINT_PERCENT = Button(area=(980, 25, 1090, 50), button=(560, 260, 730, 440), color=(0, 0, 0))

    def support(self) -> bool:
        return self.appear(DOSSIER_LIST, offset=(20, 20))

    def page(self) -> MetaPage:
        return MetaPage.DOSSIER

    def satisfy_attack_condition(self):
        return True

    def begin_meta(self) -> bool:
        if self.config.OpsiDossierBeacon_Enable and self.digit_ocr_point_and_check(self.POINT_PERCENT, 100):
            self.device.click(self.POINT_PERCENT)
        else:
            self.appear_then_click(ASH_QUIT, offset=(10, 10), interval=2)
        return True


class MetaBeaconListProcessor(MetaProcessor):

    def support(self) -> bool:
        return self.appear(BEACON_MY, offset=(20, 20))

    def page(self) -> MetaPage:
        return MetaPage.BEACON_LIST

    def get_state(self) -> MetaState:
        return MetaState.ATTACKING

    def begin_meta(self) -> bool:
        return False

    def pre_attack(self):
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

    def satisfy_attack_condition(self):
        return self.digit_ocr_point_and_check(BEACON_REMAIN, 1)


class MetaProcessorManager(UI):
    meta_main_processor: MetaProcessor
    meta_beacon_processor: MetaBeaconProcessor
    meta_dossier_processor: MetaDossierProcessor
    meta_beacon_list_processor: MetaBeaconListProcessor

    _processor_list = []

    def __init__(self, config, device):
        super().__init__(config=config, device=device)

        self.meta_main_processor = MetaProcessor(self.config, self.device)
        self._processor_list.append(self.meta_main_processor)

        self.meta_beacon_processor = MetaBeaconProcessor(self.config, self.device)
        self._processor_list.append(self.meta_beacon_processor)

        self.meta_dossier_processor = MetaDossierProcessor(self.config, self.device)
        self._processor_list.append(self.meta_dossier_processor)

        self.meta_beacon_list_processor = MetaBeaconListProcessor(self.config, self.device)
        self._processor_list.append(self.meta_beacon_list_processor)

    def ensure_meta_processor(self):
        for processor in self._processor_list:
            if processor.support():
                processor.info()
                return processor
        return None


class Meta(UI, MapEventHandler):
    meta_finish = []
    meta_processor = None
    meta_processor_manager: MetaProcessorManager

    def __init__(self, config, device):
        super().__init__(config=config, device=device)
        self.meta_processor_manager = MetaProcessorManager(config=self.config, device=self.device)

    def handle_map_event(self, drop=None):
        if super().handle_map_event(drop):
            return True
        if self.appear_then_click(META_AUTO_CONFIRM, offset=(20, 20), interval=2):
            return True

    def _ensure_processor(self):
        self.meta_processor = self.meta_processor_manager.ensure_meta_processor()
        if self.meta_processor is None:
            return False
        return True

    def attack_meta(self, expected_end):
        combat = AshCombat(config=self.config, device=self.device)
        while 1:
            self.device.screenshot()

            if self.handle_map_event():
                continue
            if not self._ensure_processor():
                continue
            state = self.meta_processor.get_state()
            if MetaState.INIT == state:
                if self.meta_processor.begin_meta():
                    continue
                else:
                    # Normal finish
                    return True
            if MetaState.ATTACKING == state:
                self.meta_processor.pre_attack()
                if self.meta_processor.satisfy_attack_condition():
                    combat.combat(expected_end=expected_end, save_get_items=False, emotion_reduce=False)
                    continue
                else:
                    # Delay finish
                    return False
            if MetaState.COMPLETE == state:
                self.appear_then_click(BEACON_REWARD, offset=(30, 30), interval=2)
                continue

    def _ensure_their_meta_page(self):
        while 1:
            self.device.screenshot()

            if self._in_self_meta_page():
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

    def _ensure_self_meta_page(self):
        while 1:
            self.device.screenshot()

            if self._in_self_meta_page():
                return True
            if self.handle_map_event():
                continue
            if self.appear_then_click(META_ENTRANCE, offset=(10, 10), interval=2):
                continue

    def _in_self_meta_page(self):
        return self.appear(ASH_SHOWDOWN, offset=(30, 30)) \
               or self.appear(BEACON_LIST, offset=(20, 20)) \
               or self.appear(DOSSIER_LIST, offset=(20, 20))

    def _in_their_meta_page(self):
        return self.appear(BEACON_MY, offset=(20, 20))

    def attack_self_meta(self):
        self._ensure_self_meta_page()
        return self.attack_meta(expected_end=self._in_self_meta_page)

    def attack_their_meta(self):
        self._ensure_their_meta_page()
        self.attack_meta(expected_end=self._in_their_meta_page)


class OpsiAshBeacon(Meta):
    def run(self):
        self.ui_ensure(page_reward)
        if self.attack_self_meta():
            self.config.task_delay(server_update=True)
        else:
            self.config.task_delay(minute=30)


class AshBeaconAssist(Meta):
    def run(self):
        self.ui_ensure(page_reward)
        self.attack_their_meta()
        self.config.task_delay(server_update=True)
