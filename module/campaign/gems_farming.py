from datetime import datetime

from module.base.decorator import cached_property
from module.campaign.campaign_base import CampaignBase
from module.campaign.run import CampaignRun
from module.combat.assets import BATTLE_PREPARATION
from module.combat.emotion import Emotion, FleetEmotion
from module.equipment.assets import *
from module.equipment.fleet_equipment import FleetEquipment
from module.exception import CampaignEnd, ScriptError
from module.handler.assets import AUTO_SEARCH_MAP_OPTION_OFF
from module.logger import logger
from module.map.assets import FLEET_PREPARATION, MAP_PREPARATION
from module.retire.assets import (
    DOCK_CHECK,
    TEMPLATE_BOGUE, TEMPLATE_HERMES, TEMPLATE_LANGLEY, TEMPLATE_RANGER,
    TEMPLATE_CASSIN_1, TEMPLATE_CASSIN_2, TEMPLATE_DOWNES_1, TEMPLATE_DOWNES_2,
    TEMPLATE_AULICK, TEMPLATE_FOOTE
)

from module.retire.dock import Dock
from module.retire.scanner import ShipScanner
from module.ui.assets import BACK_ARROW
from module.ui.page import page_fleet

SIM_VALUE = 0.92
EMOTION_LIMIT = 4


class GemsFleetEmotion(FleetEmotion):

    @property
    def limit(self):
        return EMOTION_LIMIT

    def update(self):
        self.current = self.value
        if self.current < 119:
            super().update()


class GemsEmotion(Emotion):

    def __init__(self, config):
        self.config = config
        self.fleet_1 = GemsFleetEmotion(self.config, fleet=1)
        self.fleet_2 = GemsFleetEmotion(self.config, fleet=2)
        self.fleets = [self.fleet_1, self.fleet_2]

    def check_reduce(self, battle):
        if not self.is_calculate:
            return

        if self.config.Fleet_FleetOrder == 'fleet1_standby_fleet2_all':
            battle = (0, battle * self.reduce_per_battle_before_entering)
        else:
            battle = (battle * self.reduce_per_battle_before_entering, 0)

        logger.info(f'Expect emotion reduce: {battle}')
        self.update()
        self.record()
        self.show()
        recovered = max([f.get_recovered(b) for f, b in zip(self.fleets, battle)])
        if recovered > datetime.now():
            logger.hr('EMOTION CONTROL')
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

    @cached_property
    def emotion(self) -> GemsEmotion:
        return GemsEmotion(config=self.config)


class GemsFarming(CampaignRun, FleetEquipment, Dock):

    def load_campaign(self, name, folder='campaign_main'):
        super().load_campaign(name, folder)

        class GemsCampaign(GemsCampaignOverride, self.module.Campaign):
            pass

        self.campaign: GemsCampaign = GemsCampaign(device=self.campaign.device, config=self.campaign.config)
        self.campaign.config.override(EnemyPriority_EnemyScaleBalanceWeight='S1_enemy_first')
        if self.change_flagship or self.change_vanguard:
            self.campaign.config.override(Emotion_Mode='calculate')
        else:
            self.campaign.config.override(Emotion_Mode='ignore')

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

    def set_emotion(self, emotion):
        if self.config.Fleet_FleetOrder == 'fleet1_standby_fleet2_all':
            self.campaign.config.set_record(Emotion_Fleet2Value=emotion)
        else:
            self.campaign.config.set_record(Emotion_Fleet1Value=emotion)

    def flagship_change(self):
        """
        Change flagship and flagship's equipment
        If config.GemsFarming_CommonCV == 'any', only change auxiliary equipment

        Returns:
            bool: True if flagship changed.
        """

        if self.config.GemsFarming_CommonCV == 'any':
            index_list = range(3, 5)
        else:
            index_list = range(0, 5)
        logger.hr('Change flagship', level=1)
        logger.attr('ChangeFlagship', self.config.GemsFarming_ChangeFlagship)
        self.fleet_enter(self.fleet_to_attack)
        if self.change_flagship_equip:
            logger.hr('Record flagship equipment', level=2)
            self.fleet_enter_ship(FLEET_DETAIL_ENTER_FLAGSHIP)
            self.ship_equipment_record_image(index_list=index_list)
            self.ship_equipment_take_off()
            self.fleet_back()

        logger.hr('Change flagship', level=2)
        success = self.flagship_change_execute()

        if self.change_flagship_equip:
            logger.hr('Equip flagship equipment', level=2)
            self.fleet_enter_ship(FLEET_DETAIL_ENTER_FLAGSHIP)
            self.ship_equipment_take_off()
            self.ship_equipment_take_on_image(index_list=index_list)
            self.fleet_back()

        return success

    def vanguard_change(self):
        """
        Change vanguard and vanguard's equipment

        Returns:
            bool: True if vanguard changed
        """

        logger.hr('Change vanguard', level=1)
        logger.attr('ChangeVanguard', self.config.GemsFarming_ChangeVanguard)
        self.fleet_enter(self.fleet_to_attack)
        if self.change_vanguard_equip:
            logger.hr('Record vanguard equipment', level=2)
            self.fleet_enter_ship(FLEET_DETAIL_ENTER)
            self.ship_equipment_record_image()
            self.ship_equipment_take_off()
            self.fleet_back()

        logger.hr('Change vanguard', level=2)
        success = self.vanguard_change_execute()

        if self.change_vanguard_equip:
            logger.hr('Equip vanguard equipment', level=2)
            self.fleet_enter_ship(FLEET_DETAIL_ENTER)
            self.ship_equipment_take_off()
            self.ship_equipment_take_on_image()
            self.fleet_back()

        return success

    def _dock_reset(self):
        self.dock_filter_set()
        self.dock_favourite_set(False)
        self.dock_sort_method_dsc_set()

    def _ship_change_confirm(self, button):

        self.dock_select_one(button)
        self._dock_reset()
        self.dock_select_confirm(check_button=page_fleet.check_button)

    @property
    def emotion_lower_bound(self):
        return 3 + EMOTION_LIMIT + self.campaign._map_battle * 2

    def get_common_rarity_cv(self):
        """
        Get a common rarity cv by config.GemsFarming_CommonCV
        If config.GemsFarming_CommonCV == 'any', return a common lv1 ~ lv33 cv
        Returns:
            Ship:
        """

        logger.hr('FINDING FLAGSHIP')

        scanner = ShipScanner(level=(1, 31), emotion=(self.emotion_lower_bound, 150),
                              fleet=self.fleet_to_attack, status='free')
        scanner.disable('rarity')

        if self.config.GemsFarming_CommonCV == 'any':

            self.dock_sort_method_dsc_set(False)

            ships = scanner.scan(self.device.image)
            if ships:
                # Don't need to change current
                return ships

            scanner.set_limitation(fleet=0)
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

    def get_common_rarity_dd(self):
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

        scanner = ShipScanner(level=(max_level, max_level), emotion=(self.emotion_lower_bound, 150),
                              fleet=[0, self.fleet_to_attack], status='free')
        scanner.disable('rarity')

        self.dock_sort_method_dsc_set()
        self.dock_favourite_set(self.config.GemsFarming_CommonDD == 'favourite')

        if self.config.GemsFarming_CommonDD in ['any', 'favourite', 'z20_or_z21']:
            return scanner.scan(self.device.image)

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

    def flagship_change_execute(self):
        """
        Returns:
            bool: If success.

        Pages:
            in: page_fleet
            out: page_fleet
        """
        self.ui_click(FLEET_ENTER_FLAGSHIP,
                      appear_button=page_fleet.check_button, check_button=DOCK_CHECK, skip_first_screenshot=True)
        self.dock_filter_set(
            index='cv', rarity='common', extra='enhanceable', sort='total')
        self.dock_favourite_set(False)

        ships = self.get_common_rarity_cv()
        if ships:
            ship = min(ships, key=lambda s: (s.level, -s.emotion))
            self._new_emotion_value = min(ship.emotion, self._new_emotion_value)
            self._ship_change_confirm(ship.button)

            logger.info('Change flagship success')
            return True
        else:
            logger.info('Change flagship failed, no CV in common rarity.')
            self._dock_reset()
            self.ui_back(check_button=page_fleet.check_button)
            return False

    def vanguard_change_execute(self):
        """
        Returns:
            bool: If success.

        Pages:
            in: page_fleet
            out: page_fleet
        """
        self.ui_click(FLEET_ENTER,
                      appear_button=page_fleet.check_button, check_button=DOCK_CHECK, skip_first_screenshot=True)

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

        ships = self.get_common_rarity_dd()
        if ships:
            ship = max(ships, key=lambda s: s.emotion)
            self._new_emotion_value = min(ship.emotion, self._new_emotion_value)
            self._ship_change_confirm(ship.button)

            logger.info('Change vanguard ship success')
            return True
        else:
            logger.info('Change vanguard ship failed, no DD in common rarity.')
            self._dock_reset()
            self.ui_back(check_button=page_fleet.check_button)
            return False

    _trigger_lv32 = False
    _trigger_emotion = False

    def triggered_stop_condition(self, oil_check=True):
        # Lv32 limit
        if self.change_flagship and self.campaign.config.LV32_TRIGGERED:
            self._trigger_lv32 = True
            logger.hr('TRIGGERED LV32 LIMIT')
            return True

        if self.campaign.map_is_auto_search and self.campaign.config.GEMS_EMOTION_TRIGGRED:
            self._trigger_emotion = True
            logger.hr('TRIGGERED EMOTION LIMIT')
            return True

        return super().triggered_stop_condition(oil_check=oil_check)

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
                if e.args[0] == 'Emotion withdraw' or e.args[0] == 'Emotion control':
                    self._trigger_emotion = True
                else:
                    raise e

            # End
            if self._trigger_lv32 or self._trigger_emotion:
                success = True
                self._new_emotion_value = 150
                if self.change_flagship:
                    success = self.flagship_change()
                if self.change_vanguard:
                    success = success and self.vanguard_change()

                if success and (self.change_flagship or self.change_vanguard):
                    self.set_emotion(self._new_emotion_value)

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
