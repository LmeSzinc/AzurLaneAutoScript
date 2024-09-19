from module.base.decorator import cached_property
from module.campaign.campaign_base import CampaignBase
from module.campaign.run import CampaignRun
from module.combat.assets import BATTLE_PREPARATION
from module.combat.emotion import Emotion
from module.equipment.assets import *
from module.equipment.equipment_change import EquipmentChange
from module.equipment.equipment_code import EquipmentCodeHandler
from module.equipment.fleet_equipment import OCR_FLEET_INDEX
from module.exception import CampaignEnd, ScriptError, RequestHumanTakeover
from module.handler.assets import AUTO_SEARCH_MAP_OPTION_OFF
from module.logger import logger
from module.map.assets import (FLEET_ENTER_FLAGSHIP_HARD_1,
                               FLEET_ENTER_FLAGSHIP_HARD_2, FLEET_ENTER_HARD_1, FLEET_ENTER_HARD_2,
                               FLEET_ENTER_FLAGSHIP_HARD_1_3, FLEET_ENTER_FLAGSHIP_HARD_2_3, FLEET_ENTER_HARD_1_3,
                               FLEET_ENTER_HARD_2_3)
from module.retire.assets import (
                                  DOCK_SHIP_DOWN)
from module.map.assets import FLEET_PREPARATION, MAP_PREPARATION
from module.retire.assets import (
    DOCK_CHECK,
    TEMPLATE_BOGUE, TEMPLATE_HERMES, TEMPLATE_LANGLEY, TEMPLATE_RANGER,
    TEMPLATE_CASSIN_1, TEMPLATE_CASSIN_2, TEMPLATE_DOWNES_1, TEMPLATE_DOWNES_2,
    TEMPLATE_AULICK, TEMPLATE_FOOTE
)

from module.retire.dock import Dock
from module.retire.scanner import ShipScanner
from module.ui.assets import (BACK_ARROW, FLEET_CHECK)
import inflection
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
            self.config.GEMS_EMOTION_TRIGGRED = True
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
            self.config.GEMS_EMOTION_TRIGGRED = True
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

    def current_ship(self):
        """
        Reuse templates in module.retire.assets,
        which needs different rescaling to match each current flagship.

        Pages:
            in: gear_code
        """
        if TEMPLATE_BOGUE.match(self.device.image, scaling=1.46):  # image has rotation
            return 'bogue'
        if TEMPLATE_HERMES.match(self.device.image, scaling=124/89):
            return 'hermes'
        if TEMPLATE_RANGER.match(self.device.image, scaling=4/3):
            return 'ranger'
        if TEMPLATE_LANGLEY.match(self.device.image, scaling=25/21):
            return 'langley'
        return 'DD'


class GemsFarming(CampaignRun, Dock, EquipmentChange, GemsEquipmentHandler):

    def event_hard_mode_override(self):
        HARDMODEMAPS = [
            'c1', 'c2', 'c3',
            'd1', 'd2', 'd3',
            'ht1', 'ht2', 'ht3', 'ht4', 'ht5', 'ht6',
        ]
        if inflection.underscore(self.config.Campaign_Name) in HARDMODEMAPS:
            logger.info('Is in hard mode, switch ship changing method.')
            self._ship_detail_enter = self._ship_detail_enter_hard
            self._fleet_detail_enter = self._fleet_detail_enter_hard
            self._fleet_back = self._fleet_back_hard
            self.page_fleet_check_button = FLEET_PREPARATION
            if self.config.GemsFarming_FleetNumberInHardMode == 1:
                self.FLEET_ENTER_FLAGSHIP = FLEET_ENTER_FLAGSHIP_HARD_1
                self.FLEET_ENTER = FLEET_ENTER_HARD_1
                self.FLEET_ENTER_FLAGSHIP_3_POSITION = FLEET_ENTER_FLAGSHIP_HARD_1_3
                self.FLEET_ENTER_3_POSITION = FLEET_ENTER_HARD_1_3
            elif self.config.GemsFarming_FleetNumberInHardMode == 2:
                self.FLEET_ENTER_FLAGSHIP = FLEET_ENTER_FLAGSHIP_HARD_2
                self.FLEET_ENTER = FLEET_ENTER_HARD_2
                self.FLEET_ENTER_FLAGSHIP_3_POSITION = FLEET_ENTER_FLAGSHIP_HARD_2_3
                self.FLEET_ENTER_3_POSITION = FLEET_ENTER_HARD_2_3
            else:
                logger.critical('Fleet number to change not set, check your settings')
                raise RequestHumanTakeover
            self.hard_mode = True
        else:
            self._ship_detail_enter = self._ship_detail_enter
            self._fleet_detail_enter = self._fleet_detail_enter
            self._fleet_back = self._fleet_back
            self.page_fleet_check_button = page_fleet.check_button
            self.FLEET_ENTER_FLAGSHIP = FLEET_DETAIL_ENTER_FLAGSHIP
            self._FLEET_ENTER_FLAGSHIP = self.FLEET_ENTER_FLAGSHIP
            self.FLEET_ENTER = FLEET_DETAIL_ENTER
            self._FLEET_ENTER = self.FLEET_ENTER
            self.hard_mode = False

    def load_campaign(self, name, folder='campaign_main'):
        super().load_campaign(name, folder)

        class GemsCampaign(GemsCampaignOverride, self.module.Campaign):

            @cached_property
            def emotion(self) -> GemsEmotion:
                return GemsEmotion(config=self.config)

        self.campaign = GemsCampaign(device=self.campaign.device, config=self.campaign.config)
        if self.change_flagship or self.change_vanguard:
            self.campaign.config.override(Emotion_Mode='ignore_calculate')
        else:
            self.campaign.config.override(Emotion_Mode='ignore')
        self.campaign.config.override(EnemyPriority_EnemyScaleBalanceWeight='S1_enemy_first')

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

    def _fleet_detail_enter(self):
        """
        Enter GEMS_FLEET page
        """
        self.ui_ensure(page_fleet)
        self.ui_ensure_index(self.fleet_to_attack, letter=OCR_FLEET_INDEX,
                             next_button=FLEET_NEXT, prev_button=FLEET_PREV, skip_first_screenshot=True)

    def _ship_detail_enter(self, button):
        self._fleet_detail_enter()
        self.ui_click(FLEET_DETAIL, appear_button=page_fleet.check_button,
                      check_button=FLEET_DETAIL_CHECK, skip_first_screenshot=True)
        self.equip_enter(button, long_click=False)

    def _fleet_detail_enter_hard(self):
        from module.retire.retirement import Retirement
        _retire_class = Retirement(config=self.config, device=self.device)
        self.campaign.ensure_campaign_ui(self.stage)
        button_area = self.campaign.ENTRANCE.button
        button = Button(name=str(self.stage), area=button_area, color=(0, 0, 0), button=button_area)
        for __ in range(5):
            self.campaign.ensure_campaign_ui(self.stage)
            self.ui_click(click_button=button, appear_button=BACK_ARROW, check_button=MAP_PREPARATION)
            for _ in range(30):
                self.device.screenshot()
                if self.appear_then_click(MAP_PREPARATION):
                    self.device.sleep(0.5)
                if _retire_class.handle_retirement():
                    continue
                if self.appear(button=FLEET_PREPARATION, offset=(50, 50)):
                    return
        from module.exception import GameStuckError
        raise GameStuckError

    def _ship_detail_enter_hard(self, button):
        self._fleet_detail_enter_hard()
        self.equip_enter(button)

    def _fleet_back(self):
        self.ui_back(FLEET_DETAIL_CHECK)
        self.ui_back(FLEET_CHECK)

    def _fleet_back_hard(self):
        self.ui_back(self.page_fleet_check_button)
        
    def equip_take_off(self, index_list=range(0, 5)):
        if self.config.GemsFarming_EnableEquipmentCode:
            self.clear_all_equip()
        else:
            self.ship_equipment_record_image(index_list=index_list)
            self._equip_take_off_one()

    def equip_take_on(self, index_list=range(0, 5)):
        if self.config.GemsFarming_EnableEquipmentCode:
            self.apply_equip_code()
        else:
            self._equip_take_off_one()
            self.equipment_take_on(index_list=index_list)

    def flagship_change(self):
        """
        Change flagship and flagship's equipment using gear code

        Returns:
            bool: True if flagship changed.
        """

        if self.config.GemsFarming_CommonCV in ['any', 'eagle']:
            index_list = range(3, 5)
        else:
            index_list = range(0, 5)
        logger.hr('Change flagship', level=1)
        logger.attr('ChangeFlagship', self.config.GemsFarming_ChangeFlagship)
        if self.change_flagship_equip:
            logger.hr('Unmount flagship equipments', level=2)
            self._ship_detail_enter(self.FLEET_ENTER_FLAGSHIP)
            self.equip_take_off(index_list)
            self._fleet_back() 

        logger.hr('Change flagship', level=2)
        self._fleet_detail_enter()
        success = self.flagship_change_execute()

        if self.change_flagship_equip:
            logger.hr('Mount flagship equipments', level=2)
            self._ship_detail_enter(self.FLEET_ENTER_FLAGSHIP)
            self.equip_take_on(index_list)
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
        if self.change_vanguard_equip:
            logger.hr('Unmount vanguard equipments', level=2)
            self._ship_detail_enter(self.FLEET_ENTER)
            self.equip_take_off()
            self._fleet_back()

        logger.hr('Change vanguard', level=2)
        self._fleet_detail_enter()
        success = self.vanguard_change_execute()

        if self.change_vanguard_equip:
            logger.hr('Mount vanguard equipments', level=2)
            self._ship_detail_enter(self.FLEET_ENTER)
            self.equip_take_on()
            self._fleet_back()

        return success

    def _dock_reset(self):
        self.dock_filter_set()
        self.dock_favourite_set(False)
        self.dock_sort_method_dsc_set()

    def _ship_change_confirm(self, button):

        self.dock_select_one(button)
        self._dock_reset()
        self.dock_select_confirm(check_button=self.page_fleet_check_button)

    def get_common_rarity_cv(self, lv=31, emotion=16):
        """
        Get a common rarity cv by config.GemsFarming_CommonCV
        If config.GemsFarming_CommonCV == 'any', return a common lv1 ~ lv33 cv
        Returns:
            Ship:
        """

        logger.hr('FINDING FLAGSHIP')
        emotion_lower_bound = 0 if emotion == 0 else self.emotion_lower_bound
        scanner = ShipScanner(
            level=(1, lv), emotion=(emotion_lower_bound, 150), fleet=self.fleet_to_attack, status='free')
        scanner.disable('rarity')

        if self.config.GemsFarming_CommonCV in ['any', 'eagle']:

            self.dock_sort_method_dsc_set()

            ships = scanner.scan(self.device.image)
            if ships:
                # Don't need to change current
                return ships

            scanner.set_limitation(fleet=0)

            common_cv = {
                'Bogue': TEMPLATE_BOGUE,
                'Ranger': TEMPLATE_RANGER,
                'Langley': TEMPLATE_LANGLEY
            }
            if self.config.GemsFarming_CommonCV == 'any':
                common_cv['Hermes'] = TEMPLATE_HERMES

            for name, template in common_cv.items():
                logger.info(f'Search for CV {name}.')
                self.dock_sort_method_dsc_set()

                candidates = [ship for ship in scanner.scan(self.device.image, output=False)
                              if template.match(self.image_crop(ship.button, copy=False), similarity=SIM_VALUE)]

                if candidates:
                    return candidates

                logger.info(f'No suitable CV {name} was found, try reversed order.')
                self.dock_sort_method_dsc_set(False)

                candidates = [ship for ship in scanner.scan(self.device.image)
                              if template.match(self.image_crop(ship.button, copy=False), similarity=SIM_VALUE)]

                if candidates:
                    return candidates

            self.dock_sort_method_dsc_set(False)
            return scanner.scan(self.device.image, output=False)

        else:
            template = {
                'BOGUE': TEMPLATE_BOGUE,
                'HERMES': TEMPLATE_HERMES,
                'LANGLEY': TEMPLATE_LANGLEY,
                'RANGER': TEMPLATE_RANGER
            }[f'{self.config.GemsFarming_CommonCV.upper()}']

            self.dock_sort_method_dsc_set()

            ships = scanner.scan(self.device.image)
            if ships:
                # Don't need to change current
                return ships

            scanner.set_limitation(fleet=0)
            candidates = [ship for ship in scanner.scan(self.device.image, output=False)
                          if template.match(self.image_crop(ship.button, copy=False), similarity=SIM_VALUE)]

            if candidates:
                return candidates

            logger.info('No specific CV was found, try reversed order.')
            self.dock_sort_method_dsc_set(False)

            candidates = [ship for ship in scanner.scan(self.device.image)
                          if template.match(self.image_crop(ship.button, copy=False), similarity=SIM_VALUE)]

            return candidates

    def get_common_rarity_dd(self, emotion=16):
        """
        Get a common rarity dd with level is 100 (70 for servers except CN) 
        and emotion >= self.emotion_lower_bound
        Returns:
            Ship:
        """
        logger.hr('FINDING VANGUARD')

        if self.config.SERVER in ['cn']:
            max_level = 100
        else:
            max_level = 70
        from module.gg_handler.gg_data import GGData
        _ggdata = GGData(self.config).get_data()
        if _ggdata['gg_enable'] and _ggdata['gg_auto'] and self.config.GemsFarming_ALLowLowVanguardLevel:
            min_level = 2
        else:
            min_level = max_level
        if self.hard_mode:
            min_level = max(min_level, 49)
        emotion_lower_bound = 0 if emotion == 0 else self.emotion_lower_bound
        scanner = ShipScanner(level=(min_level, max_level), emotion=(emotion_lower_bound, 150),
                              fleet=self.fleet_to_attack, status='free')
        scanner.disable('rarity')

        self.dock_sort_method_dsc_set()

        ships = scanner.scan(self.device.image)
        if ships:
            # Don't need to change current
            return ships

        scanner.set_limitation(fleet=0)
        self.dock_favourite_set(self.config.GemsFarming_CommonDD == 'favourite')

        if self.config.GemsFarming_CommonDD in ['any', 'favourite', 'z20_or_z21']:
            return scanner.scan(self.device.image, output=False)
        
        candidates = self.find_candidates(self.get_templates(self.config.GemsFarming_CommonDD), scanner)

        if candidates:
            return candidates
        
        logger.info('No specific DD was found, try reversed order.')
        self.dock_sort_method_dsc_set(False)

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

    def solve_hard_flagship_black(self):
        if self.hard_mode:
            self.ui_click(self.FLEET_ENTER_FLAGSHIP,
                          appear_button=self.page_fleet_check_button, check_button=DOCK_CHECK,
                          skip_first_screenshot=True)
            if self.appear(DOCK_SHIP_DOWN):
                self.ui_click(DOCK_SHIP_DOWN,
                              appear_button=DOCK_CHECK, check_button=self.page_fleet_check_button,
                              skip_first_screenshot=True)
            else:
                self.ui_back(check_button=FLEET_PREPARATION)
            self._FLEET_ENTER_FLAGSHIP = self.FLEET_ENTER_FLAGSHIP
            self.FLEET_ENTER_FLAGSHIP = self.FLEET_ENTER_FLAGSHIP_3_POSITION

    def flagship_change_execute(self):
        """
        Returns:
            bool: If success.

        Pages:
            in: page_fleet
            out: page_fleet
        """
        self.solve_hard_flagship_black()
        self.FLEET_ENTER_FLAGSHIP = FLEET_ENTER_FLAGSHIP if not self.hard_mode else self.FLEET_ENTER_FLAGSHIP
        self.ui_click(self.FLEET_ENTER_FLAGSHIP,
                      appear_button=self.page_fleet_check_button, check_button=DOCK_CHECK, skip_first_screenshot=True)
        self.FLEET_ENTER_FLAGSHIP = self._FLEET_ENTER_FLAGSHIP if not self.hard_mode else self.FLEET_ENTER_FLAGSHIP
        faction = 'eagle' if self.config.GemsFarming_CommonCV == 'eagle' else 'all'
        self.dock_filter_set(
            index='cv', rarity='common', faction=faction, extra='enhanceable', sort='total')
        self.dock_favourite_set(False)

        ship = self.get_common_rarity_cv()
        if ship:
            self._ship_change_confirm(min(ship, key=lambda s: (s.level, -s.emotion)).button)

            if self.hard_mode:
                self.FLEET_ENTER_FLAGSHIP = self._FLEET_ENTER_FLAGSHIP

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
                self._ship_change_confirm(min(ship, key=lambda s: (s.level, -s.emotion)).button)
            else:
                if self.hard_mode:
                    raise RequestHumanTakeover
                self._dock_reset()
                self.ui_back(check_button=self.page_fleet_check_button)
            if self.hard_mode:
                self.FLEET_ENTER_FLAGSHIP = self._FLEET_ENTER_FLAGSHIP
            return False

    def solve_hard_vanguard_black(self):
        if self.hard_mode:
            self.ui_click(self.FLEET_ENTER,
                          appear_button=self.page_fleet_check_button, check_button=DOCK_CHECK,
                          skip_first_screenshot=True)
            if self.appear(DOCK_SHIP_DOWN):
                self.ui_click(DOCK_SHIP_DOWN,
                              appear_button=DOCK_CHECK, check_button=self.page_fleet_check_button,
                              skip_first_screenshot=True)
            else:
                self.ui_back(check_button=FLEET_PREPARATION)
            self._FLEET_ENTER = self.FLEET_ENTER
            self.FLEET_ENTER = self.FLEET_ENTER_3_POSITION

    def vanguard_change_execute(self):
        """
        Returns:
            bool: If success.

        Pages:
            in: page_fleet
            out: page_fleet
        """
        self.solve_hard_vanguard_black()
        self.FLEET_ENTER = FLEET_ENTER if not self.hard_mode else self.FLEET_ENTER
        self.ui_click(self.FLEET_ENTER,
                      appear_button=self.page_fleet_check_button, check_button=DOCK_CHECK, skip_first_screenshot=True)
        self.FLEET_ENTER = self._FLEET_ENTER if not self.hard_mode else self.FLEET_ENTER
        if self.config.GemsFarming_CommonDD == 'any':
            faction = ['eagle', 'iron']
        elif self.config.GemsFarming_CommonDD == 'favourite':
            faction = 'all'
        elif self.config.GemsFarming_CommonDD == 'z20_or_z21':
            faction = 'iron'
        elif self.config.GemsFarming_CommonDD in ['aulick_or_foote', 'cassin_or_downes']:
            faction = 'eagle'
        else:
            logger.error(f'Invalid CommonDD setting: {self.config.GemsFarming_CommonDD}')
            raise ScriptError('Invalid GemsFarming_CommonDD')
        self.dock_filter_set(
            index='dd', rarity='common', faction=faction, extra='can_limit_break')
        self.dock_favourite_set(False)

        ship = self.get_common_rarity_dd()
        if ship:
            if self.hard_mode:
                self.FLEET_ENTER = self._FLEET_ENTER
            target_ship = max(ship, key=lambda s: s.emotion)
            self.set_emotion(target_ship.emotion)
            self._ship_change_confirm(target_ship.button)

            logger.info('Change vanguard ship success')
            return True
        else:
            logger.info('Change vanguard ship failed, no DD in common rarity.')

            ship = self.get_common_rarity_dd(emotion=0)
            if ship and self.hard_mode:
                target_ship = max(ship, key=lambda s: s.emotion)
                self.set_emotion(target_ship.emotion)
                self._ship_change_confirm(target_ship.button)
            else:
                if self.hard_mode:
                    raise RequestHumanTakeover
                self._dock_reset()
                self.ui_back(check_button=self.page_fleet_check_button)
            if self.hard_mode:
                self.FLEET_ENTER = self._FLEET_ENTER
            return False

    _trigger_lv32 = False
    _trigger_emotion = False

    def triggered_stop_condition(self, oil_check=True):
        # Lv32 limit
        if self.change_flagship and self.campaign.config.LV32_TRIGGERED:
            self._trigger_lv32 = True
            logger.hr('TRIGGERED LV32 LIMIT')
            return True

        if self.campaign.config.GEMS_EMOTION_TRIGGRED:
            self._trigger_emotion = True
            logger.hr('TRIGGERED EMOTION LIMIT')
            return True

        return super().triggered_stop_condition(oil_check=oil_check)

    def set_emotion(self, emotion):
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
        self.campaign_floder = folder
        self.event_hard_mode_override()
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
                    if (e.args[0] == 'Hard not satisfied' and
                            str(self.config.GemsFarming_FleetNumberInHardMode) in e.args[1]):
                        if self.change_flagship and self.change_vanguard:
                            self.flagship_change()
                            self.vanguard_change()
                        else:
                            raise RequestHumanTakeover
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
                self._trigger_emotion = False
                self.campaign.config.LV32_TRIGGERED = False
                self.campaign.config.GEMS_EMOTION_TRIGGRED = False

                # Scheduler
                if self.config.task_switched():
                    self.campaign.ensure_auto_search_exit()
                    self.config.task_stop()
                elif not success:
                    self.campaign.ensure_auto_search_exit()
                    self.config.task_delay(minute=30)
                    self.config.task_stop()

                continue
            else:
                break
