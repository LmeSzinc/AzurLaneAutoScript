from module.base.decorator import cached_property
from module.campaign.campaign_base import CampaignBase
from module.campaign.run import CampaignRun
from module.combat.assets import BATTLE_PREPARATION
from module.combat.emotion import Emotion
from module.equipment.assets import *
from module.equipment.equipment_code import EquipmentCodeHandler
from module.equipment.fleet_equipment import OCR_FLEET_INDEX
from module.exception import CampaignEnd, ScriptError, RequestHumanTakeover
from module.handler.assets import AUTO_SEARCH_MAP_OPTION_OFF
from module.logger import logger
from module.map.assets import FLEET_PREPARATION, MAP_PREPARATION
from module.retire.assets import (
    DOCK_CHECK, DOCK_SHIP_DOWN,
    TEMPLATE_BOGUE, TEMPLATE_HERMES, TEMPLATE_LANGLEY, TEMPLATE_RANGER,
    TEMPLATE_CASSIN_1, TEMPLATE_CASSIN_2, TEMPLATE_DOWNES_1, TEMPLATE_DOWNES_2,
    TEMPLATE_AULICK, TEMPLATE_FOOTE
)
from module.retire.retirement import Retirement, TEMPLATE_COMMON_CV
from module.retire.scanner import ShipScanner
from module.ui.assets import BACK_ARROW, FLEET_CHECK
from module.ui.page import page_fleet

SIM_VALUE = 0.92


class GemsEmotion(Emotion):

    def check_reduce(self, battle):
        """
        Overwrite emotion.check_reduce()
        Check emotion before entering a campaign.
        Args:
            battle (int): Battles in this campaign
        Raise:
            CampaignEnd: Pause current task to prevent emotion control in the future.
        """

        if not self.is_calculate:
            return

        recovered, delay = self._check_reduce(battle)
        if delay:
            self.config.GEMS_EMOTION_TRIGGERED = True
            logger.info('Detect low emotion, pause current task')
            raise CampaignEnd('Emotion control')

    def wait(self, fleet_index):
        pass


class GemsCampaignOverride(CampaignBase):

    def handle_combat_low_emotion(self):
        """
        Overwrite info_handler.handle_combat_low_emotion()
        If change vanguard is enabled, withdraw combat and change flagship and vanguard
        """
        if self.config.GemsFarming_ChangeVanguard == 'disabled':
            result = self.handle_popup_confirm('IGNORE_LOW_EMOTION')
            if result:
                # Avoid clicking AUTO_SEARCH_MAP_OPTION_OFF
                self.interval_reset(AUTO_SEARCH_MAP_OPTION_OFF)
            return result

        if self.handle_popup_cancel('IGNORE_LOW_EMOTION'):
            self.config.GEMS_EMOTION_TRIGGERED = True
            logger.hr('EMOTION WITHDRAW')

            while 1:
                self.device.screenshot()

                if self.handle_story_skip():
                    continue
                if self.handle_popup_cancel('IGNORE_LOW_EMOTION'):
                    continue

                if self.appear(BATTLE_PREPARATION, offset=(20, 20), interval=2):
                    self.device.click(BACK_ARROW)
                    continue
                if self.handle_auto_search_exit():
                    continue
                if self.is_in_stage():
                    break

                if self.is_in_map():
                    self.withdraw()
                    break

                if self.appear(FLEET_PREPARATION, offset=(20, 50), interval=2) \
                        or self.appear(MAP_PREPARATION, offset=(20, 20), interval=2):
                    self.enter_map_cancel()
                    break
            raise CampaignEnd('Emotion withdraw')


class GemsEquipmentHandler(EquipmentCodeHandler):

    def __init__(self, config, device=None, task=None):
        super().__init__(config=config,
                         device=device,
                         task=task,
                         key="GemsFarming.GemsFarming.EquipmentCode",
                         ships=['DD', 'bogue', 'hermes', 'langley', 'ranger'])

    def current_ship(self, skip_first_screenshot=True):
        """
        Reuse templates in module.retire.assets,
        which needs different rescaling to match each current flagship.

        Pages:
            in: gear_code
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            
            # End
            if not self.appear(EMPTY_SHIP_R):
                break
            else:
                logger.info('Waiting ship icon loading.')

        if TEMPLATE_BOGUE.match(self.device.image, scaling=1.46):  # image has rotation
            return 'bogue'
        if TEMPLATE_HERMES.match(self.device.image, scaling=124/89):
            return 'hermes'
        if TEMPLATE_RANGER.match(self.device.image, scaling=4/3):
            return 'ranger'
        if TEMPLATE_LANGLEY.match(self.device.image, scaling=25/21):
            return 'langley'
        return 'DD'


class GemsFarming(CampaignRun, GemsEquipmentHandler, Retirement):
    def hard_mode_override(self):
        if self.campaign.config.Campaign_Mode == 'hard':
            logger.info('Is in hard mode, switch ship changing method.')
            self.hard_mode = True
            self._ship_detail_enter = self._ship_detail_enter_hard
            self._fleet_detail_enter = self._fleet_detail_enter_hard
            self._fleet_back = self._fleet_back_hard
            self.page_fleet_check_button = FLEET_PREPARATION
            if self.config.Fleet_FleetOrder == 'fleet1_standby_fleet2_all':
                self.fleet_detail_enter_flagship = FLEET_DETAIL_ENTER_FLAGSHIP_HARD_2
                self.fleet_enter_flagship = FLEET_ENTER_FLAGSHIP_HARD_2
                self.fleet_detail_enter = FLEET_DETAIL_ENTER_HARD_2
                self.fleet_enter = FLEET_ENTER_HARD_2
            else:
                self.fleet_detail_enter_flagship = FLEET_DETAIL_ENTER_FLAGSHIP_HARD_1
                self.fleet_enter_flagship = FLEET_ENTER_FLAGSHIP_HARD_1
                self.fleet_detail_enter = FLEET_DETAIL_ENTER_HARD_1
                self.fleet_enter = FLEET_ENTER_HARD_1
        else:
            self.hard_mode = False
            self.page_fleet_check_button = page_fleet.check_button
            self.fleet_detail_enter_flagship = FLEET_DETAIL_ENTER_FLAGSHIP
            self.fleet_detail_enter = FLEET_DETAIL_ENTER
            self.fleet_enter_flagship = FLEET_ENTER_FLAGSHIP
            self.fleet_enter = FLEET_ENTER

    def load_campaign(self, name, folder='campaign_main'):
        super().load_campaign(name, folder)

        class GemsCampaign(GemsCampaignOverride, self.module.Campaign):

            @cached_property
            def emotion(self) -> GemsEmotion:
                return GemsEmotion(config=self.config)

        self.campaign = GemsCampaign(device=self.campaign.device, config=self.campaign.config)
        if self.change_vanguard:
            self.campaign.config.override(Emotion_Mode='ignore_calculate')
        else:
            self.campaign.config.override(Emotion_Mode='ignore')

    @property
    def emotion_lower_bound(self):
        return 4 + self.campaign._map_battle * 2

    @property
    def change_flagship(self):
        return 'ship' in self.config.GemsFarming_ChangeFlagship

    @property
    def change_flagship_equip(self):
        return 'equip' in self.config.GemsFarming_ChangeFlagship

    @property
    def change_vanguard(self):
        return 'ship' in self.config.GemsFarming_ChangeVanguard

    @property
    def change_vanguard_equip(self):
        return 'equip' in self.config.GemsFarming_ChangeVanguard

    @property
    def fleet_to_attack(self):
        if self.config.Fleet_FleetOrder == 'fleet1_standby_fleet2_all':
            return self.config.Fleet_Fleet2
        else:
            return self.config.Fleet_Fleet1

    def _fleet_detail_enter(self, fleet):
        self.ui_ensure(page_fleet)
        self.ui_ensure_index(fleet, letter=OCR_FLEET_INDEX,
                             next_button=FLEET_NEXT, prev_button=FLEET_PREV, skip_first_screenshot=True)

    def _ship_detail_enter(self, button):
        self.ui_click(FLEET_DETAIL, appear_button=page_fleet.check_button,
                      check_button=FLEET_DETAIL_CHECK, skip_first_screenshot=True)
        self.equip_enter(button, long_click=False)

    def _fleet_detail_enter_hard(self, fleet):
        if self.appear(FLEET_PREPARATION, offset=(20, 50)):
            return
        self.campaign.ensure_campaign_ui(self.stage)
        self.ui_click(click_button=self.campaign.ENTRANCE, appear_button=BACK_ARROW, check_button=MAP_PREPARATION)
        while 1:
            self.device.screenshot()

            if self.appear_then_click(MAP_PREPARATION, interval=1):
                continue

            if self.handle_retirement():
                continue

            if self.appear(FLEET_PREPARATION, offset=(20, 50)):
                break

    def _ship_detail_enter_hard(self, button):
        self.equip_enter(button)

    def _fleet_back(self):
        self.ui_back(FLEET_DETAIL_CHECK)
        self.ui_back(FLEET_CHECK)

    def _fleet_back_hard(self):
        self.ui_back(self.page_fleet_check_button)

    def flagship_change(self):
        """
        Change flagship and flagship's equipment using gear code

        Returns:
            bool: True if flagship changed.
        """
        logger.hr('Change flagship', level=1)
        logger.attr('ChangeFlagship', self.config.GemsFarming_ChangeFlagship)
        self._fleet_detail_enter(self.fleet_to_attack)
        if self.change_flagship_equip:
            logger.hr('Unmount flagship equipments', level=2)
            self._ship_detail_enter(self.fleet_detail_enter_flagship)
            self.clear_all_equip()
            self._fleet_back() 

        logger.hr('Change flagship', level=2)
        success = self.flagship_change_execute()

        if self.change_flagship_equip:
            logger.hr('Mount flagship equipments', level=2)
            self._ship_detail_enter(self.fleet_detail_enter_flagship)
            self.apply_equip_code()
            self._fleet_back()

        return success

    def vanguard_change(self):
        """
        Change vanguard and vanguard's equipment using gear code

        Returns:
            bool: True if vanguard changed
        """
        logger.hr('Change vanguard', level=1)
        logger.attr('ChangeVanguard', self.config.GemsFarming_ChangeVanguard)
        self._fleet_detail_enter(self.fleet_to_attack)
        if self.change_vanguard_equip:
            logger.hr('Unmount vanguard equipments', level=2)
            self._ship_detail_enter(self.fleet_detail_enter)
            self.clear_all_equip()
            self._fleet_back()

        logger.hr('Change vanguard', level=2)
        success = self.vanguard_change_execute()

        if self.change_vanguard_equip:
            logger.hr('Mount vanguard equipments', level=2)
            self._ship_detail_enter(self.fleet_detail_enter)
            self.apply_equip_code()
            self._fleet_back()

        return success

    def _dock_reset(self):
        self.dock_favourite_set(False, wait_loading=False)
        self.dock_sort_method_dsc_set(wait_loading=False)
        self.dock_filter_set()

    def _ship_change_confirm(self, button):
        self.dock_select_one(button)
        self._dock_reset()
        self.dock_select_confirm(check_button=self.page_fleet_check_button)

    def get_common_rarity_cv(self, lv=31, emotion=16):
        """
        Get a common rarity cv by config.GemsFarming_CommonCV
        If config.GemsFarming_CommonCV == 'any', return a common lv1 ~ lv33 cv

        _dock_reset() needs to be called later.

        Args:
            lv (int): max level of common cv
            emotion (int): min emotion of common cv
        Returns:
            Ship:
        """
        faction = 'eagle' if self.config.GemsFarming_CommonCV == 'eagle' else 'all'
        extra = 'can_limit_break' if self.config.GemsFarming_ALLowHighFlagshipLevel else 'enhanceable'
        self.dock_favourite_set(False, wait_loading=False)
        self.dock_sort_method_dsc_set(False, wait_loading=False)
        self.dock_filter_set(
            index='cv', rarity='common', faction=faction, extra=extra, sort='total')

        logger.hr('FINDING FLAGSHIP')

        if self.config.GemsFarming_ALLowHighFlagshipLevel:
            if self.config.SERVER in ['cn']:
                max_level = 100
            else:
                max_level = 70
            min_level = max_level
        else:
            max_level = lv
            min_level = 1
        emotion_lower_bound = 0 if emotion == 0 else self.emotion_lower_bound
        scanner = ShipScanner(
            level=(min_level, max_level), emotion=(emotion_lower_bound, 150), fleet=self.fleet_to_attack, status='free')
        scanner.disable('rarity')

        if self.config.GemsFarming_CommonCV in ['any', 'eagle']:

            ships = scanner.scan(self.device.image)
            if ships:
                # Don't need to change current
                return ships

            # Change to any ship
            scanner.set_limitation(fleet=0)

            logger.info(f'Search for Common CV.')
            common_cv = self.get_common_cv_filter(self.config.GemsFarming_CommonCVFilter)
            find_first = True
            common_cv_candidates = {}
            for name in common_cv:
                template = TEMPLATE_COMMON_CV[name.upper()]
                candidates = [ship for ship in scanner.scan(self.device.image, output=False)
                              if template.match(self.image_crop(ship.button, copy=False), similarity=SIM_VALUE)]

                if find_first:
                    find_first = False
                    if candidates:
                        logger.info(f'Find Common CV {name}.')
                        return candidates

                common_cv_candidates[name] = candidates

            logger.info(f'No suitable CV was found, try reversed order.')
            self.dock_sort_method_dsc_set(True)

            for name in common_cv:
                template = TEMPLATE_COMMON_CV[name.upper()]
                candidates = [ship for ship in scanner.scan(self.device.image, output=False)
                              if template.match(self.image_crop(ship.button, copy=False), similarity=SIM_VALUE)]

                if candidates:
                    logger.info(f'Find Common CV {name}.')
                    return candidates
                elif common_cv_candidates[name]:
                    logger.info(f'Find Common CV {name}.')
                    return common_cv_candidates[name]

            return scanner.scan(self.device.image, output=False)

        else:
            template = TEMPLATE_COMMON_CV[f'{self.config.GemsFarming_CommonCV.upper()}']

            ships = scanner.scan(self.device.image)
            if ships:
                # Don't need to change current
                return ships

            scanner.set_limitation(fleet=0)
            candidates = [ship for ship in scanner.scan(self.device.image, output=False)
                          if template.match(self.image_crop(ship.button, copy=False), similarity=SIM_VALUE)]

            if candidates:
                # Change to specific ship
                return candidates

            logger.info('No specific CV was found, try reversed order.')
            self.dock_sort_method_dsc_set(True)

            candidates = [ship for ship in scanner.scan(self.device.image)
                          if template.match(self.image_crop(ship.button, copy=False), similarity=SIM_VALUE)]

            return candidates

    def get_common_rarity_dd(self, emotion=16):
        """
        Get a common rarity dd with level is 100 (70 for servers except CN) 
        and emotion >= self.emotion_lower_bound

        _dock_reset() needs to be called later.

        Args:
            emotion (int): min emotion of common dd
        Returns:
            Ship:
        """
        rarity = 'common'
        extra = 'can_limit_break'
        if self.config.GemsFarming_CommonDD == 'any':
            faction = ['eagle', 'iron']
        elif self.config.GemsFarming_CommonDD == 'favourite':
            faction = 'all'
        elif self.config.GemsFarming_CommonDD == 'z20_or_z21':
            faction = 'iron'
        elif self.config.GemsFarming_CommonDD == 'DDG':
            faction = 'dragon'
            rarity = 'super_rare'
            extra = 'no_limit'
        elif self.config.GemsFarming_CommonDD in ['aulick_or_foote', 'cassin_or_downes']:
            faction = 'eagle'
        else:
            logger.error(f'Invalid CommonDD setting: {self.config.GemsFarming_CommonDD}')
            raise ScriptError('Invalid GemsFarming_CommonDD')
        favourite = self.config.GemsFarming_CommonDD == 'favourite'
        self.dock_favourite_set(favourite, wait_loading=False)
        self.dock_sort_method_dsc_set(True, wait_loading=False)
        self.dock_filter_set(
            index='dd', rarity=rarity, faction=faction, extra=extra)

        logger.hr('FINDING VANGUARD')

        if self.config.SERVER in ['cn']:
            max_level = 100
        else:
            max_level = 70
        if self.config.GemsFarming_CommonDD == 'DDG':
            max_level = 125
        if self.config.GemsFarming_ALLowLowVanguardLevel:
            min_level = 30
        else:
            min_level = max_level
        if self.hard_mode:
            min_level = max(min_level, 70)
        emotion_lower_bound = 0 if emotion == 0 else self.emotion_lower_bound
        scanner = ShipScanner(level=(min_level, max_level), emotion=(emotion_lower_bound, 150),
                              fleet=[0, self.fleet_to_attack], status='free')
        scanner.disable('rarity')

        if self.config.GemsFarming_CommonDD in ['any', 'favourite', 'z20_or_z21', 'DDG']:
            # Change to any ship
            return scanner.scan(self.device.image)

        candidates = self.find_candidates(self.get_templates(self.config.GemsFarming_CommonDD), scanner)

        if candidates:
            # Change to specific ship
            return candidates

        logger.info('No specific DD was found, try reversed order.')
        self.dock_sort_method_dsc_set(False)

        # Change specific ship
        candidates = self.find_candidates(self.get_templates(self.config.GemsFarming_CommonDD), scanner)
        return candidates

    def find_candidates(self, template, scanner):
        """
        Find candidates based on template matching using a scanner.

        """
        candidates = []
        for item in template:
            candidates = [ship for ship in scanner.scan(self.device.image, output=False)
                          if item.match(self.image_crop(ship.button, copy=False), similarity=SIM_VALUE)]
            if candidates:
                break
        return candidates

    @staticmethod
    def get_templates(common_dd):
        """
        Returns the corresponding template list based on CommonDD
        """
        if common_dd == 'aulick_or_foote':
            return [
                TEMPLATE_AULICK,
                TEMPLATE_FOOTE
            ]
        elif common_dd == 'cassin_or_downes':
            return [
                TEMPLATE_CASSIN_1, TEMPLATE_CASSIN_2,
                TEMPLATE_DOWNES_1, TEMPLATE_DOWNES_2
            ]
        else:
            logger.error(f'Invalid CommonDD setting: {common_dd}')
            raise ScriptError(f'Invalid CommonDD setting: {common_dd}')

    def ship_down_hard(self, button):
        """
        In hard mode, let the ship leave the fleet first
        """
        if self.hard_mode:
            self.ui_click(button,
                          appear_button=self.page_fleet_check_button, check_button=DOCK_CHECK, skip_first_screenshot=True)
            if self.appear(DOCK_SHIP_DOWN):
                self.ui_click(DOCK_SHIP_DOWN,
                              appear_button=DOCK_CHECK, check_button=self.page_fleet_check_button, skip_first_screenshot=True)
            else:
                self.ui_back(check_button=FLEET_PREPARATION)

    def flagship_change_with_emotion(self, ship):
        """
        Change flagship and calculate emotion
        """
        target_ship = max(ship, key=lambda s: (s.level, s.emotion))
        if self.config.GemsFarming_ALLowHighFlagshipLevel:
            self.set_emotion(target_ship.emotion)
        self._ship_change_confirm(target_ship.button)

    def flagship_change_execute(self):
        """
        Returns:
            bool: If success.

        Pages:
            in: page_fleet
            out: page_fleet
        """
        self.ship_down_hard(self.fleet_detail_enter_flagship)
        self.ui_click(self.fleet_enter_flagship,
                      appear_button=self.page_fleet_check_button, check_button=DOCK_CHECK, skip_first_screenshot=True)

        ship = self.get_common_rarity_cv()
        if ship:
            self.flagship_change_with_emotion(ship)
            logger.info('Change flagship success')
            return True
        else:
            logger.info('Change flagship failed, no CV in common rarity.')

            if self.config.SERVER in ['cn']:
                max_level = 100
            else:
                max_level = 70
            ship = self.get_common_rarity_cv(lv=max_level, emotion=0)
            if ship and self.hard_mode:
                self.flagship_change_with_emotion(ship)
            else:
                if self.hard_mode:
                    raise RequestHumanTakeover
                self._dock_reset()
                self.ui_back(check_button=self.page_fleet_check_button)
            return False

    def vanguard_change_with_emotion(self, ship):
        """
        Change vanguard and calculate emotion
        """
        target_ship = max(ship, key=lambda s: s.emotion)
        if self.config.GemsFarming_ALLowHighFlagshipLevel:
            self.set_emotion(min(self.get_emotion(), target_ship.emotion))
        else:
            self.set_emotion(target_ship.emotion)
        self._ship_change_confirm(target_ship.button)

    def vanguard_change_execute(self):
        """
        Returns:
            bool: If success.

        Pages:
            in: page_fleet
            out: page_fleet
        """
        self.ship_down_hard(self.fleet_detail_enter)
        self.ui_click(self.fleet_enter,
                      appear_button=self.page_fleet_check_button, check_button=DOCK_CHECK, skip_first_screenshot=True)

        ship = self.get_common_rarity_dd()
        if ship:
            self.vanguard_change_with_emotion(ship)
            logger.info('Change vanguard ship success')
            return True
        else:
            logger.info('Change vanguard ship failed, no DD in common rarity.')

            ship = self.get_common_rarity_dd(emotion=0)
            if ship and self.hard_mode:
                self.vanguard_change_with_emotion(ship)
            else:
                if self.hard_mode:
                    raise RequestHumanTakeover
                self._dock_reset()
                self.ui_back(check_button=self.page_fleet_check_button)
            return False

    _trigger_lv32 = False
    _trigger_emotion = False

    def triggered_stop_condition(self, oil_check=True):
        # Lv32 limit
        if self.change_flagship and self.campaign.config.LV32_TRIGGERED \
                and not self.config.GemsFarming_ALLowHighFlagshipLevel:
            self._trigger_lv32 = True
            logger.hr('TRIGGERED LV32 LIMIT')
            return True

        if self.campaign.config.GEMS_EMOTION_TRIGGERED:
            self._trigger_emotion = True
            logger.hr('TRIGGERED EMOTION LIMIT')
            return True

        return super().triggered_stop_condition(oil_check=oil_check)

    def get_emotion(self):
        """
        Get fleet emotion value from config
        """
        if self.config.Fleet_FleetOrder == 'fleet1_standby_fleet2_all':
            return self.campaign.config.Emotion_Fleet2Value
        else:
            return self.campaign.config.Emotion_Fleet1Value

    def set_emotion(self, emotion):
        """
        Set fleet emotion value
        """
        if self.config.Fleet_FleetOrder == 'fleet1_standby_fleet2_all':
            self.campaign.config.set_record(Emotion_Fleet2Value=emotion)
        else:
            self.campaign.config.set_record(Emotion_Fleet1Value=emotion)

    def run(self, name, folder='campaign_main', mode='normal', total=0):
        """
        Args:
            name (str): Name of .py file.
            folder (str): Name of the file folder under campaign.
            mode (str): `normal` or `hard`
            total (int):
        """
        self.config.STOP_IF_REACH_LV32 = self.change_flagship
        while 1:
            self._trigger_lv32 = False
            is_limit = self.config.StopCondition_RunCount
            try:
                super().run(name=name, folder=folder, total=total)
            except CampaignEnd as e:
                if e.args[0] in ['Emotion withdraw', 'Emotion control']:
                    self._trigger_emotion = True
                else:
                    raise e
            except RequestHumanTakeover as e:
                try:
                    if e.args[0] == 'Hard not satisfied' and self.change_flagship and self.change_vanguard:
                        self.hard_mode_override()
                        self.flagship_change()
                        self.vanguard_change()
                    else:
                        raise RequestHumanTakeover
                except RequestHumanTakeover as e:
                    raise RequestHumanTakeover
                except Exception as e:
                    from module.exception import GameStuckError
                    raise GameStuckError

            # End
            if self._trigger_lv32 or self._trigger_emotion:
                success = True
                self.hard_mode_override()
                if self.change_flagship:
                    success = self.flagship_change()
                if self.change_vanguard:
                    success = success and self.vanguard_change()

                if is_limit and self.config.StopCondition_RunCount <= 0:
                    logger.hr('Triggered stop condition: Run count')
                    self.config.StopCondition_RunCount = 0
                    self.config.Scheduler_Enable = False
                    break

                self._trigger_lv32 = False
                self.campaign.config.LV32_TRIGGERED = False
                self.campaign.config.GEMS_EMOTION_TRIGGERED = False

                # Scheduler
                if self.config.task_switched():
                    self._trigger_emotion = False
                    self.campaign.ensure_auto_search_exit()
                    self.config.task_stop()
                elif not success and (self.config.GemsFarming_DelayTaskIFNoFlagship \
                        or self._trigger_emotion):
                    self._trigger_emotion = False
                    self.campaign.ensure_auto_search_exit()
                    self.config.task_delay(minute=30)
                    self.config.task_stop()

                self._trigger_emotion = False
                continue
            else:
                break
