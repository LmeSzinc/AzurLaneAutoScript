from abc import ABCMeta, abstractmethod
from module.campaign.campaign_base import CampaignBase
from module.campaign.run import CampaignRun
from module.config.config import AzurLaneConfig
from module.equipment.assets import *
from module.equipment.equipment_change import EquipmentChange
from module.equipment.fleet_equipment import FleetEquipment
from module.exception import ScriptError, RequestHumanTakeover
from module.logger import logger
from module.map.assets import FLEET_PREPARATION, MAP_PREPARATION
from module.map.map_operation import MapOperation
from module.retire.assets import (
    DOCK_CHECK, DOCK_SHIP_DOWN,
    TEMPLATE_BOGUE, TEMPLATE_HERMES, TEMPLATE_LANGLEY, TEMPLATE_RANGER,
    TEMPLATE_CASSIN_1, TEMPLATE_CASSIN_2, TEMPLATE_DOWNES_1, TEMPLATE_DOWNES_2,
    TEMPLATE_AULICK, TEMPLATE_FOOTE
)
from module.retire.dock import Dock
from module.retire.scanner import ShipScanner
from module.ui.assets import BACK_ARROW
from module.ui.page import page_fleet

SIM_VALUE = 0.92


class ShipChange(CampaignRun, Dock, EquipmentChange, metaclass=ABCMeta):
    config: AzurLaneConfig
    # Will be overridden in NormalShipChange and HardShipChange
    fleet_to_attack: int
    page_fleet_check_button: Button
    flagship_detail_enter: Button
    vanguard_detail_enter: Button
    flagship_enter: Button
    vanguard_enter: Button

    @abstractmethod
    def fleet_enter(self):
        pass

    @abstractmethod
    def fleet_enter_ship(self, button):
        pass

    @abstractmethod
    def fleet_back(self):
        pass

    @abstractmethod
    def dock_ship_down(self, button):
        pass

    @abstractmethod
    def after_flagship_change_failed(self):
        pass

    @abstractmethod
    def after_vanguard_change_failed(self):
        pass

    @property
    def change_flagship_equip(self):
        return 'equip' in self.config.GemsFarming_ChangeFlagship

    @property
    def change_vanguard_equip(self):
        return 'equip' in self.config.GemsFarming_ChangeVanguard

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
        self.fleet_enter()
        if self.change_flagship_equip:
            logger.hr('Record flagship equipment', level=2)
            self.fleet_enter_ship(self.flagship_detail_enter)
            self.ship_equipment_record_image(index_list=index_list)
            self.ship_equipment_take_off()
            self.fleet_back()

        logger.hr('Change flagship', level=2)
        success = self.flagship_change_execute()

        if self.change_flagship_equip:
            logger.hr('Equip flagship equipment', level=2)
            self.fleet_enter_ship(self.flagship_detail_enter)
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
        self.fleet_enter()
        if self.change_vanguard_equip:
            logger.hr('Record vanguard equipment', level=2)
            self.fleet_enter_ship(self.vanguard_detail_enter)
            self.ship_equipment_record_image()
            self.ship_equipment_take_off()
            self.fleet_back()

        logger.hr('Change vanguard', level=2)
        success = self.vanguard_change_execute()

        if self.change_vanguard_equip:
            logger.hr('Equip vanguard equipment', level=2)
            self.fleet_enter_ship(self.vanguard_detail_enter)
            self.ship_equipment_take_off()
            self.ship_equipment_take_on_image()
            self.fleet_back()

        return success

    def _dock_reset(self):
        self.dock_favourite_set(False, wait_loading=False)
        self.dock_sort_method_dsc_set(wait_loading=False)
        self.dock_filter_set()

    def _ship_change_confirm(self, button):
        self.dock_select_one(button)
        self._dock_reset()
        self.dock_select_confirm(check_button=self.page_fleet_check_button)

    def get_common_rarity_cv(self, level=31, emotion=10):
        """
        Get a common rarity cv by config.GemsFarming_CommonCV
        If config.GemsFarming_CommonCV == 'any', return a common lv1 ~ lv33 cv

        _dock_reset() needs to be called later.

        Returns:
            Ship:
        """
        self.dock_favourite_set(False, wait_loading=False)
        self.dock_sort_method_dsc_set(False, wait_loading=False)
        self.dock_filter_set(
            index='cv', rarity='common', extra='enhanceable', sort='total')

        logger.hr('FINDING FLAGSHIP')

        scanner = ShipScanner(level=(1, level), emotion=(emotion, 150),
                              fleet=self.fleet_to_attack, status='free')
        scanner.disable('rarity')

        if self.config.GemsFarming_CommonCV == 'any':

            ships = scanner.scan(self.device.image)
            if ships:
                # Don't need to change current
                return ships

            # Change to any ship
            scanner.set_limitation(fleet=0)
            return scanner.scan(self.device.image, output=False)

        else:
            template = {
                'BOGUE': TEMPLATE_BOGUE,
                'HERMES': TEMPLATE_HERMES,
                'LANGLEY': TEMPLATE_LANGLEY,
                'RANGER': TEMPLATE_RANGER
            }[f'{self.config.GemsFarming_CommonCV.upper()}']

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

    def get_common_rarity_dd(self, emotion=10):
        """
        Get a common rarity dd with level is 100 (70 for servers except CN) and emotion > 10

        _dock_reset() needs to be called later.

        Returns:
            Ship:
        """
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
        favourite = self.config.GemsFarming_CommonDD == 'favourite'
        self.dock_favourite_set(favourite, wait_loading=False)
        self.dock_sort_method_dsc_set(True, wait_loading=False)
        self.dock_filter_set(
            index='dd', rarity='common', faction=faction, extra='can_limit_break')

        logger.hr('FINDING VANGUARD')

        if self.config.SERVER in ['cn']:
            max_level = 100
        else:
            max_level = 70

        scanner = ShipScanner(level=(max_level, max_level), emotion=(emotion, 150),
                              fleet=self.fleet_to_attack, status='free')
        scanner.disable('rarity')

        ships = scanner.scan(self.device.image)
        if ships:
            # Don't need to change current
            return ships

        scanner.set_limitation(fleet=0)
        if self.config.GemsFarming_CommonDD in ['any', 'favourite', 'z20_or_z21']:
            # Change to any ship
            return scanner.scan(self.device.image, output=False)

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

    def flagship_change_execute(self):
        """
        Returns:
            bool: If success.

        Pages:
            in: page_fleet
            out: page_fleet
        """
        self.dock_ship_down(self.flagship_detail_enter)
        self.ui_click(self.flagship_enter,
                      appear_button=self.page_fleet_check_button, check_button=DOCK_CHECK, skip_first_screenshot=True)

        ship = self.get_common_rarity_cv()
        if ship:
            self._ship_change_confirm(min(ship, key=lambda s: (s.level, -s.emotion)).button)

            logger.info('Change flagship success')
            return True
        else:
            logger.info('Change flagship failed, no CV in common rarity.')
            self.after_flagship_change_failed()
            return False

    def vanguard_change_execute(self):
        """
        Returns:
            bool: If success.

        Pages:
            in: page_fleet
            out: page_fleet
        """
        self.dock_ship_down(self.vanguard_detail_enter)
        self.ui_click(self.vanguard_enter,
                      appear_button=self.page_fleet_check_button, check_button=DOCK_CHECK, skip_first_screenshot=True)

        ship = self.get_common_rarity_dd()
        if ship:
            self._ship_change_confirm(max(ship, key=lambda s: s.emotion).button)

            logger.info('Change vanguard ship success')
            return True
        else:
            logger.info('Change vanguard ship failed, no DD in common rarity.')
            self.after_vanguard_change_failed()
            return False


class NormalShipChange(FleetEquipment, ShipChange):
    @property
    def fleet_to_attack(self):
        if self.config.Fleet_FleetOrder == 'fleet1_standby_fleet2_all':
            return self.config.Fleet_Fleet2
        else:
            return self.config.Fleet_Fleet1

    @property
    def page_fleet_check_button(self):
        return page_fleet.check_button

    @property
    def flagship_detail_enter(self):
        return FLEET_DETAIL_ENTER_FLAGSHIP

    @property
    def vanguard_detail_enter(self):
        return FLEET_DETAIL_ENTER

    @property
    def flagship_enter(self):
        return FLEET_ENTER_FLAGSHIP

    @property
    def vanguard_enter(self):
        return FLEET_ENTER

    def fleet_enter(self):
        super().fleet_enter(self.fleet_to_attack)

    def fleet_enter_ship(self, button):
        super().fleet_enter_ship(button)

    def fleet_back(self):
        super().fleet_back()

    def dock_ship_down(self, button):
        """
        Don't need to down ship in normal mode
        """
        pass

    def after_flagship_change_failed(self):
        self._dock_reset()
        self.ui_back(check_button=page_fleet.check_button)

    def after_vanguard_change_failed(self):
        self.after_flagship_change_failed()


class HardShipChange(MapOperation, ShipChange):
    def __init__(self, campaign=None, stage=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.campaign: CampaignBase = campaign
        self.config = self.campaign.config
        self.stage: str = stage

    @property
    def fleet_to_attack(self):
        return 2 if self.config.Fleet_FleetOrder == 'fleet1_standby_fleet2_all' else 1

    @property
    def page_fleet_check_button(self):
        return FLEET_PREPARATION

    @property
    def flagship_detail_enter(self):
        return globals()[f'FLEET_DETAIL_ENTER_FLAGSHIP_HARD_{self.fleet_to_attack}']

    @property
    def vanguard_detail_enter(self):
        return globals()[f'FLEET_DETAIL_ENTER_HARD_{self.fleet_to_attack}']

    @property
    def flagship_enter(self):
        return globals()[f'FLEET_ENTER_FLAGSHIP_HARD_{self.fleet_to_attack}']

    @property
    def vanguard_enter(self):
        return globals()[f'FLEET_ENTER_HARD_{self.fleet_to_attack}']

    def fleet_enter(self):
        if self.appear(FLEET_PREPARATION, offset=(20, 50)):
            return
        self.campaign.ensure_campaign_ui(self.stage)
        self.ui_click(click_button=self.campaign.ENTRANCE,
                      appear_button=BACK_ARROW, check_button=MAP_PREPARATION)
        while 1:
            self.device.screenshot()

            if self.handle_map_mode_switch('hard') and self.appear_then_click(MAP_PREPARATION, interval=1):
                continue

            if self.handle_retirement():
                continue

            if self.appear(FLEET_PREPARATION, offset=(20, 50)):
                break

    def fleet_enter_ship(self, button):
        self.ship_info_enter(button)

    def fleet_back(self):
        self.ui_back(FLEET_PREPARATION)

    def dock_ship_down(self, button):
        """
        In hard mode, let the ship leave the fleet first
        """
        self.ui_click(button,
                        appear_button=FLEET_PREPARATION, check_button=DOCK_CHECK, skip_first_screenshot=True)
        if self.appear(DOCK_SHIP_DOWN):
            self.ui_click(DOCK_SHIP_DOWN,
                            appear_button=DOCK_CHECK, check_button=FLEET_PREPARATION, skip_first_screenshot=True)
        else:
            self.ui_back(check_button=FLEET_PREPARATION)

    def after_flagship_change_failed(self):
        """
        In hard mode, should still put a ship in the fleet if there is no available ship
        """
        max_level = 100 if self.config.SERVER in ['cn'] else 70
        ship = self.get_common_rarity_cv(level=max_level, emotion=0)
        if ship:
            self._ship_change_confirm(min(ship, key=lambda s: (s.level, -s.emotion)).button)
        else:
            raise RequestHumanTakeover
        
    def after_vanguard_change_failed(self):
        """
        In hard mode, should still put a ship in the fleet if there is no available ship
        """
        ship = self.get_common_rarity_dd(emotion=0)
        if ship:
            self._ship_change_confirm(max(ship, key=lambda s: s.emotion).button)
        else:
            raise RequestHumanTakeover
