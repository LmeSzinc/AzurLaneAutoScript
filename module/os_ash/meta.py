import re
from enum import Enum

import module.config.server as server
from module.base.timer import Timer
from module.combat.combat import BATTLE_PREPARATION
from module.logger import logger
from module.meta_reward.meta_reward import MetaReward
from module.ocr.ocr import Digit, DigitCounter
from module.os_ash.ash import AshCombat
from module.os_ash.assets import *
from module.os_handler.map_event import MapEventHandler
from module.ui.assets import BACK_ARROW
from module.ui.page import page_reward
from module.ui.ui import UI


class MetaState(Enum):
    INIT = 'no meta begin'
    ATTACKING = 'a meta under attack'
    COMPLETE = 'reward to be collected'
    UNDEFINED = 'a undefined page'


OCR_BEACON_TIER = Digit(BEACON_TIER, name='OCR_ASH_TIER')
if server.server != 'jp':
    OCR_META_DAMAGE = Digit(META_DAMAGE, name='OCR_META_DAMAGE')
else:
    OCR_META_DAMAGE = Digit(META_DAMAGE, letter=(201, 201, 201), name='OCR_META_DAMAGE')


class MetaDigitCounter(DigitCounter):
    def after_process(self, result):
        result = super().after_process(result)

        # 00/200 -> 100/200
        if result.startswith('00/'):
            result = '100/' + result[3:]

        # 23 -> 2/3
        if re.match(r'^[0123]3$', result):
            result = f'{result[0]}/{result[1]}'

        return result


class Meta(UI, MapEventHandler):

    def digit_ocr_point_and_check(self, button: Button, check_number: int):
        if server.server != 'jp':
            point_ocr = MetaDigitCounter(button, letter=(235, 235, 235), threshold=160, name='POINT_OCR')
        else:
            point_ocr = MetaDigitCounter(button, letter=(192, 192, 192), threshold=160, name='POINT_OCR')
        point, _, _ = point_ocr.ocr(self.device.image)
        if point >= check_number:
            return True
        return False

    def handle_map_event(self, drop=None):
        if super().handle_map_event(drop):
            return True
        if self.appear_then_click(META_AUTO_CONFIRM, offset=(20, 20), interval=2):
            logger.info('Find auto attack complete')
            return True
        if self.appear(HELP_CONFIRM, offset=(30, 30), interval=2):
            logger.info('Accidentally click HELP_ENTER')
            self.device.click(BACK_ARROW)
            return True
        if self.appear(BATTLE_PREPARATION, offset=(30, 30), interval=2):
            logger.info('Wrong click into battle preparation page')
            self.device.click(BACK_ARROW)
            return True
        if self.handle_popup_cancel('META'):
            return True
        if self.appear_then_click(META_ENTRANCE, offset=(20, 300), interval=2):
            return True
        return False


def _server_support():
    return server.server in ['cn', 'en', 'jp', 'tw']


def _server_support_dossier_auto_attack():
    return server.server in ['cn', 'en']


class OpsiAshBeacon(Meta):
    _meta_receive = []
    _meta_category = "undefined"

    def _attack_meta(self, skip_first_screenshot=True):
        """
        Handle all META attack events.

        Pages:
            in: in_meta
            out: in_meta
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_map_event():
                continue
            state = self._get_state()
            logger.info('Meta state:' + state.name)
            if MetaState.UNDEFINED == state:
                continue
            if MetaState.INIT == state:
                if self._begin_meta():
                    continue
                else:
                    # Normal finish
                    break
            if MetaState.ATTACKING == state:
                if not self._pre_attack():
                    continue
                if self._satisfy_attack_condition():
                    self._make_an_attack()
                    continue
            if MetaState.COMPLETE == state:
                self._handle_ash_beacon_reward()
                if not self._meta_category in self._meta_receive:
                    self._meta_receive.append(self._meta_category)
                # Check other tasks after kill a meta
                self.config.check_task_switch()
                continue

    def _make_an_attack(self):
        """
        Handle a meta combat.

        Pages:
            in: in_meta, ASH_START
            out: in_meta, ASH_START or BEACON_REWARD
        """
        logger.hr('Begin meta combat', level=2)

        def expected_end():
            if self.appear(BATTLE_PREPARATION, offset=(30, 30), interval=2):
                logger.info('Wrong click into battle preparation page')
                self.device.click(BACK_ARROW)
                return False
            if self.appear(HELP_CONFIRM, offset=(30, 30), interval=3):
                logger.info('Wrong click into HELP_CONFIRM')
                self.device.click(HELP_ENTER)
                return False
            if self._in_meta_page():
                logger.info('Meta combat finished and in correct page.')
                return True

            return False

        # Attack
        combat = AshCombat(config=self.config, device=self.device)
        combat.combat(expected_end=expected_end, save_get_items=False, emotion_reduce=False)

    def _handle_ash_beacon_reward(self, skip_first_screenshot=True):
        """
        Reward meta.

        Pages:
            in: in_meta, BEACON_REWARD
            out: in_meta
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if not self.appear(BEACON_REWARD, offset=(30, 30)):
                if self._in_meta_page():
                    break

            if self.appear_then_click(BEACON_REWARD, offset=(30, 30), interval=2):
                logger.info('Reap meta rewards')
                continue
            # Finish random events
            if self.handle_map_event():
                continue
            # Accidentally goto main page
            if self.ui_main_appear_then_click(page_reward, interval=2):
                continue
            if self.appear(META_ENTRANCE, offset=(20, 300), interval=2):
                continue

    def _satisfy_attack_condition(self):
        """
        Check whether this meta can be attacked.
        In beacon:
            when enable OneHitMode and has attacked, not allow attack.
        In Dossier:
            when enable autoAttack, not allow attack
        """
        if self.appear(BEACON_LIST, offset=(20, 20)):
            # Enable OneHitMode and had attack this meta
            if _server_support() and self.config.OpsiAshBeacon_OneHitMode:
                damage = self._get_meta_damage()
                if damage > 0:
                    logger.info('Enable OneHitMode and meta damage is ' + str(damage) + ', check after 30 minutes')
                    self.config.task_delay(minute=30)
                    self.config.task_stop()
        if self.appear(DOSSIER_LIST, offset=(20, 20)):
            # Meta is Auto Attacking
            if self.appear(META_AUTO_ATTACKING, offset=(20, 20)):
                logger.info('This meta is auto attacking, check after 15 minutes')
                self.config.task_delay(minute=15)
                self.config.task_stop()
        return True

    def _get_meta_damage(self):
        """
        Get the damage the from current meta
        """
        self._ensure_meta_inner_page_damage()
        return OCR_META_DAMAGE.ocr(self.device.image)

    def _ensure_meta_inner_page_damage(self, skip_first_screenshot=True):
        """
        Switch inner page ensure in damage, not information.

        Pages:
            in: in_meta, ASH_START
            out: in_meta, META_INNER_PAGE_DAMAGE, ASH_START
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.match_template_color(META_INNER_PAGE_DAMAGE, offset=(20, 20)):
                logger.info('Already in meta damage page')
                break
            if self.match_template_color(META_INNER_PAGE_NOT_DAMAGE, offset=(20, 20)):
                logger.info('In meta details page, should switch to damage page')
                self.appear_then_click(META_INNER_PAGE_NOT_DAMAGE, offset=(20, 20), interval=2)
                continue

    def _pre_attack(self):
        """
        Some pre_attack preparations, including recording meta category.
        In beacon:
            ask for help if needed
        In dossier:
            ['cn', 'en']: auto attack if needed
            others: do nothing this version
        """
        # Page beacon or dossier
        if self.appear(BEACON_LIST, offset=(20, 20)):
            self._meta_category = "beacon"
            if self.config.OpsiAshBeacon_OneHitMode or self.config.OpsiAshBeacon_RequestAssist:
                if not self._ask_for_help():
                    return False
            return True
        if self.appear(DOSSIER_LIST, offset=(20, 20)):
            self._meta_category = "dossier"
            # can auto attack but not auto attacking
            if _server_support_dossier_auto_attack() and self.config.OpsiAshBeacon_DossierAutoAttackMode \
                    and self.appear(META_AUTO_ATTACK_START, offset=(5, 5)):
                return self._dossier_auto_attack()
            return True
        return False

    def _ask_for_help(self):
        """
        Request help from friends, guild and world.

        Returns:
            bool: Whether success to call assist.
                False if META finished just after calling assist.

        Pages:
            in: is_in_meta
            out: is_in_meta
        """
        # Enter help page
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(HELP_CONFIRM, offset=(20, 20)):
                break
            # Click
            if self.appear_then_click(HELP_ENTER, offset=(20, 20), interval=3):
                continue
            # Wrongly entered BATTLE_PREPARATION
            if self.appear(BATTLE_PREPARATION, offset=(30, 30), interval=2):
                self.device.click(BACK_ARROW)
                continue

        # Here use simple clicks. Dropping some clicks is acceptable, no need to confirm they are selected.
        self.device.click(HELP_3)
        self.device.sleep((0.1, 0.3))
        self.device.click(HELP_2)
        self.device.sleep((0.1, 0.3))
        self.device.click(HELP_1)

        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(HELP_ENTER, offset=(30, 30)):
                return True
            if self.appear(BEACON_REWARD, offset=(30, 30)):
                logger.info('META finished just after calling assist, ignore meta assist')
                return False
            # Click
            if self.appear_then_click(HELP_CONFIRM, offset=(30, 30), interval=3):
                continue

    def _dossier_auto_attack(self):
        """
        Auto attack dossier

        Returns:
            bool: Whether success to do auto attack.

        Pages:
            in: is_in_meta & not auto attacking
            out: is_in_meta
        """
        timeout = Timer(10, count=20).start()
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(META_AUTO_ATTACKING, offset=(5, 5)):
                return True
            if timeout.reached():
                logger.warning('Run _dossier_auto_attack timeout, probably because META_AUTO_ATTACK_START was missing')
                return False
            # Finished by others
            if self.appear(BEACON_REWARD, offset=(30, 30)):
                return False

            # Click
            if self.appear_then_click(META_AUTO_ATTACK_CONFIRM, offset=(5, 5), interval=3):
                continue
            if self.appear_then_click(META_AUTO_ATTACK_START, offset=(5, 5), interval=3):
                continue
            # Wrongly entered BATTLE_PREPARATION
            if self.appear(BATTLE_PREPARATION, offset=(30, 30), interval=2):
                self.device.click(BACK_ARROW)
                continue

    def _begin_meta(self):
        """
        No matter which meta page you are in, start or select a meta.
        In meta main:
            select beacon or dossier entrance into if needed, or end task
        In beacon or dossier:
            begin a new meta if needed, or back to meta main page
        """
        # Page meta main
        if self.appear(ASH_SHOWDOWN, offset=(30, 30), interval=2):
            # Beacon
            if self._check_beacon_point():
                self.device.click(META_MAIN_BEACON_ENTRANCE)
                logger.info('Select beacon entrance into')
                return True
            # Dossier
            if _server_support() \
                    and self.config.OpsiAshBeacon_AttackMode == 'current_dossier' \
                    and self._check_dossier_point():
                if self.appear_then_click(META_MAIN_DOSSIER_ENTRANCE, offset=(20, 20), interval=2):
                    logger.info('Select dossier entrance into')
                    return True
                else:
                    logger.info('None dossier has been selected')
            return False
        # Page beacon
        elif self.appear(BEACON_LIST, offset=(20, 20), interval=2):
            if self._check_beacon_point():
                self.device.click(META_BEGIN_ENTRANCE)
                logger.info('Begin a beacon')
            return True
        # Page dossier
        elif _server_support() \
                and self.appear(DOSSIER_LIST, offset=(20, 20), interval=2):
            if self.config.OpsiAshBeacon_AttackMode == 'current_dossier' \
                    and self._check_dossier_point():
                if self.appear_then_click(META_BEGIN_ENTRANCE, offset=(20, 20), interval=2):
                    logger.info('Begin a dossier')
                    return True
                else:
                    logger.info('None dossier has been selected')
            self.appear_then_click(ASH_QUIT, offset=(10, 10), interval=2)
            return True
        # UnKnown Page
        else:
            return True

    def _check_beacon_point(self) -> bool:
        if self.appear(META_BEACON_FLAG, offset=(180, 20)):
            META_BEACON_DATA.load_offset(META_BEACON_FLAG)
            return self.digit_ocr_point_and_check(META_BEACON_DATA.button, 100)
        return False

    def _check_dossier_point(self) -> bool:
        if self.appear(META_DOSSIER_FLAG, offset=(180, 20)):
            META_DOSSIER_DATA.load_offset(META_DOSSIER_FLAG)
            return self.digit_ocr_point_and_check(META_DOSSIER_DATA.button, 100)
        return False

    def _get_state(self):
        # Page UnKnown
        if not self._in_meta_page():
            return MetaState.UNDEFINED
        # Page beacon or dossier
        elif self.appear(BEACON_LIST, offset=(20, 20)) \
                or self.appear(DOSSIER_LIST, offset=(20, 20)):
            if self.appear(HELP_ENTER, offset=(30, 30)):
                return MetaState.ATTACKING
            elif self.appear(BEACON_REWARD, offset=(20, 20)):
                return MetaState.COMPLETE
            return MetaState.INIT
        elif self.appear(ASH_SHOWDOWN, offset=(30, 30)):
            return MetaState.INIT
        return MetaState.UNDEFINED

    def _in_meta_page(self):
        return self.appear(ASH_SHOWDOWN, offset=(30, 30)) \
               or self.appear(BEACON_LIST, offset=(20, 20)) \
               or self.appear(DOSSIER_LIST, offset=(20, 20))

    def _ensure_meta_page(self, skip_first_screenshot=True):
        logger.info('Ensure beacon attack page')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._in_meta_page():
                logger.info('In meta page')
                return True
            if self.handle_map_event():
                continue
            if self.appear_then_click(META_ENTRANCE, offset=(20, 300), interval=2):
                continue

    def ensure_dossier_page(self, skip_first_screenshot=True):
        self.ui_ensure(page_reward)
        self._ensure_meta_page()
        logger.info('Ensure dossier meta page')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(DOSSIER_LIST, offset=(20, 20)):
                logger.info('In dossier page')
                return True
            if self.handle_map_event():
                continue
            if self.appear(ASH_SHOWDOWN, offset=(30, 30)):
                self.device.click(META_MAIN_DOSSIER_ENTRANCE)
                continue

    def _begin_beacon(self):
        logger.hr('Meta Beacon Attack')
        if not _server_support():
            logger.info("Server not support dossier beacon and OneHitMode, please contact the developer.")
        self._ensure_meta_page()
        self._attack_meta()

    def run(self):
        self.ui_ensure(page_reward)
        self._begin_beacon()

        with self.config.multi_set():
            for meta in self._meta_receive:
                MetaReward(self.config, self.device).run(category=meta)
            self._meta_receive = []
            self.config.task_delay(server_update=True)


class AshBeaconAssist(Meta):
    def _attack_meta(self, skip_first_screenshot=True):
        timeout = Timer(3, count=9).start()
        appeared = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if not appeared and timeout.reached():
                logger.info('No meta beacon found, delay task OpsiAshAssist')
                break

            if self.handle_map_event():
                continue
            if self.appear(ASH_START, offset=(20, 20)):
                appeared = True
                remain_times = self.digit_ocr_point_and_check(BEACON_REMAIN, 1)
                if remain_times:
                    self._ensure_meta_level()
                    self._make_an_attack()
                else:
                    logger.info('No enough assist times, complete')
                    break

        return appeared

    def _make_an_attack(self):
        """
        Handle a meta assist combat.

        Pages:
            in: in_meta_assist
            out: in_meta_assist
        """
        logger.hr('Begin meta assist combat', level=2)

        def expected_end():
            if self.appear(BATTLE_PREPARATION, offset=(30, 30), interval=2):
                logger.info('Wrong click into battle preparation page')
                self.device.click(BACK_ARROW)
                return False
            # AL redirects to unfinished self beacon after assist, so switch back
            if self.appear_then_click(BEACON_LIST, offset=(-20, -5, 300, 5), interval=2):
                return False
            if self.appear(ASH_SHOWDOWN, offset=(30, 30), interval=2):
                logger.info('Meta combat finished at ASH_SHOWDOWN.')
                self.device.click(META_MAIN_BEACON_ENTRANCE)
            if self._in_meta_assist_page():
                logger.info('Meta combat finished and in correct page.')
                return True

            return False

        # Attack
        combat = AshCombat(config=self.config, device=self.device)
        combat.combat(expected_end=expected_end, save_get_items=False, emotion_reduce=False)

    def _ensure_meta_level(self):
        """
        Select an meta whose level satisfies
        """
        # Ensure BEACON_TIER shown up
        # When entering beacon list, tier number wasn't shown immediately.
        tier = self.config.OpsiAshAssist_Tier
        logger.info('Begin find a level ' + str(tier) + ' meta')
        for n in range(10):
            if self.image_color_count(BEACON_TIER, color=(0, 0, 0), threshold=221, count=50):
                break

            self.device.screenshot()
            if n >= 9:
                logger.warning('Waiting for beacon tier timeout')
        # Select beacon
        current = -1
        for _ in range(5):
            current = OCR_BEACON_TIER.ocr(self.device.image)
            if current >= tier:
                break
            else:
                self.device.click(BEACON_NEXT)
                self.device.sleep((0.3, 0.5))
                self.device.screenshot()
        if current < tier:
            logger.info(f'Tier {tier} beacon not found after 5 trial, use current beacon')
        logger.info('Find a beacon in level:' + str(current))

    def _in_meta_assist_page(self):
        return self.appear(BEACON_MY, offset=(20, 20))

    def _ensure_meta_assist_page(self, skip_first_screenshot=True):
        logger.info('Ensure beacon assist page')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._in_meta_assist_page():
                logger.info('In beacon assist page')
                return True
            if self.handle_map_event():
                continue
            if self.appear_then_click(META_ENTRANCE, offset=(20, 300), interval=2):
                continue
            if self.appear(ASH_SHOWDOWN, offset=(20, 20), interval=2):
                self.device.click(META_MAIN_BEACON_ENTRANCE)
                logger.info('In meta page main')
                continue
            if self.appear_then_click(BEACON_LIST, offset=(300, 20), interval=2):
                continue
            if self.appear_then_click(DOSSIER_LIST, offset=(20, 20), interval=2):
                logger.info('In meta page dossier')
                continue

    def _begin_meta_assist(self):
        logger.hr('Meta Beacon Assist')
        self._ensure_meta_assist_page()
        return self._attack_meta(skip_first_screenshot=False)

    def run(self):
        self.ui_ensure(page_reward)

        if self._begin_meta_assist():
            MetaReward(self.config, self.device).run()
            self.config.task_delay(server_update=True)
        else:
            self.config.task_delay(minute=(10, 20))
