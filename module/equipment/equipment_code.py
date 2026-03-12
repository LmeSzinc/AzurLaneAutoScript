import re
import yaml

from module.config.config import AzurLaneConfig
from module.equipment.assets import *
from module.exception import RequestHumanTakeover
from module.logger import logger
from module.storage.assets import EQUIPMENT_FULL
from module.storage.storage import StorageHandler


BASE64_REGEX = re.compile('^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$')
EMPTY_GEAR_CODE = "MC8wLzAvMC8wXDA="

def is_equip_code(string):
    """
    Checks if current string is None or BASE64 string.
    """
    if string is None:
        return True
    if not isinstance(string, str):
        return False
    return BASE64_REGEX.match(string)


class EquipmentCode:
    config: AzurLaneConfig
    config_key: str
    coded_ships: list
    
    def __setattr__(self, key, value):
        if key in ['config', 'config_key', 'coded_ships']:
            super().__setattr__(key, value)
        elif key in self.coded_ships:
            if is_equip_code(value):
                super().__setattr__(key, value)
            else:
                logger.error(f'{value} is not a gear code, skip setting {key}')
        else:
            logger.error(f'{key} is not in coded ships: {self.coded_ships}')

    def __init__(self, config, key, ships):
        """
        Args:
            config (AzurLaneConfig):
            key: location of config containing gear code configs
            ships (list of string): ships whose gear codes should be memorized
        """
        self.config = config
        self.config_key = key
        self.coded_ships = ships
        _config = config.cross_get(keys=key)
        codes = dict([(ship, None) for ship in self.coded_ships])
        for line in _config.splitlines():
            try:
                codes.update(yaml.safe_load(line))
            except Exception as e:
                logger.error(f'Failed to parse current line of the config: "{line}", skipping')
        for ship in self.coded_ships:
            code: str = codes.pop(ship, None)
            self.__setattr__(ship, code)

    def export_to_config(self):
        """
        Export current ships' gear codes to location {self.config_key} of {self.config}.
        """
        _config = {}
        for ship in self.coded_ships:
            _config.update({ship: self.__getattribute__(ship)})
        value = yaml.safe_dump(_config)
        logger.info(f'Gear code configs to be exported: {value}')
        self.config.cross_set(keys=self.config_key, value=value)


class EquipmentCodeHandler(StorageHandler):
    codes: EquipmentCode

    def __init__(self, config, key, ships, device=None, task=None):
        super().__init__(config, device=device, task=task)
        self.codes = EquipmentCode(self.config, key=key, ships=ships)

    def enter_equip_code_page(self, skip_first_screenshot=True):
        """
        Pages:
            in: ship_detail
            out: gear_code
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(EQUIPMENT_CODE_PAGE_CHECK, offset=(5, 5)):
                break

            if self.appear_then_click(EQUIPMENT_CODE_ENTRANCE, offset=(5, 5)):
                continue

    # def exit_equip_code_page(self):
    #     """
    #     Pages:
    #         in: gear_code
    #         out: ship_detail
    #     """
    #     self.ui_back(check_button=EQUIPMENT_CODE_ENTRANCE)

    def current_ship(self, **kwargs):
        # Will be overridden in subclasses.
        pass

    def click_export_button(self, skip_first_screenshot=True):
        self.handle_info_bar()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.info_bar_count():
                break

            if self.appear_then_click(EQUIPMENT_CODE_EXPORT, offset=(5, 5), interval=1):
                continue

    def export_equip_code(self, ship=None):
        """
        Export current ship's gear code to config file.
        This is done by first using "export" button 
        to export gear code to clipboard,
        then update the config file using yaml.safe_dump().
        """
        code = self.device.clipboard
        if code == EMPTY_GEAR_CODE:
            logger.info('Detect 0/0/0/0/0\\0 code, continue exporting.')
        logger.attr("Gear code", code)
        if not ship in self.codes.coded_ships:
            ship = self.current_ship()
        logger.attr("Current ship", ship)
        logger.info(f'Set gear code of {ship} to be {code}')
        self.codes.__setattr__(ship, code)
        self.codes.export_to_config()

    def equip_preview_empty(self):
        if self.appear(EQUIPMENT_CODE_EQUIP_5_LOCKED):
            max_index = 5
        else:
            max_index = 6
        for index in range(max_index):
            if not self.appear(globals()['EQUIPMENT_CODE_EQUIP_{index}'.format(index=index)], offset=(5, 5)):
                return False
        
        return True
    
    def clear_equip_preview(self, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.equip_preview_empty():
                logger.info('Confirm equipment preview cleared.')
                break

            if self.appear_then_click(EQUIPMENT_CODE_CLEAR, offset=(5, 5)):
                continue

    def enter_equip_code_input_mode(self, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(EQUIPMENT_CODE_ENTER, offset=(5, 5)):
                self.device.click(EQUIPMENT_CODE_TEXTBOX)
                continue

            # End
            if self.device.ime_shown():
                break

    def confirm_equip_code(self, skip_first_screenshot=False):
        check_counter = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(EQUIPMENT_CODE_ENTER, offset=(5, 5), interval=1):
                continue

            # End
            if not self.equip_preview_empty():
                logger.info('Confirm gear code loaded.')
                return True
            else:
                check_counter += 1
                if check_counter >= 5:
                    logger.error('Gear code load failed, retrying.')
                    return False

    def confirm_equip_preview(self, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(EQUIPMENT_CODE_CONFIRM, offset=(5, 5), interval=5):
                continue

            if self.handle_popup_confirm('EQUIPMENT_CODE'):
                continue

            # End
            if self.appear(EQUIPMENT_CODE_ENTRANCE, offset=(5, 5)):
                return True
            if self.appear(EQUIPMENT_FULL, offset=(30, 30)):
                return False

    def clear_all_equip(self):
        self.enter_equip_code_page()
        ship = self.current_ship()
        self.device.u2_set_fastinput_ime(True)
        logger.attr("Current_ime", self.device.u2_current_ime())
        self.click_export_button()
        if self.codes.__getattribute__(ship) is None:
            self.export_equip_code(ship)
        self.clear_equip_preview()
        for _ in range(5):
            success = self.confirm_equip_preview()
            if success:
                return True
            else:
                self.handle_storage_full()
                self.clear_equip_preview()

        raise RequestHumanTakeover(
            f'Failed to clear all equipment for {ship}, please check manually.'
        )

    def apply_equip_code(self, code=None):
        self.enter_equip_code_page()
        self.clear_equip_preview()
        if code is None:
            ship = self.current_ship()
            code = self.codes.__getattribute__(ship)
            if code is None:
                code = self.device.clipboard  # assuming clipboard is not modified
            logger.info(f'Apply gear code {code} for {ship}')
        else:
            logger.info(f'Forcefully apply gear code {code} to current ship.')
        for _ in range(5):
            if code is not None and code != EMPTY_GEAR_CODE:
                self.enter_equip_code_input_mode()
                self.device.text_input_and_confirm(code, clear=True)
                success = self.confirm_equip_code()
                if not success:
                    continue
            success = self.confirm_equip_preview()
            if success:
                logger.info("Gear code import complete.")
                return True
            else:
                self.handle_storage_full()
                self.clear_equip_preview()

        raise RequestHumanTakeover(
            f'Failed to apply equipment for {ship}, please check manually.'
        )
