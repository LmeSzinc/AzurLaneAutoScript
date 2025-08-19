from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.logger import logger
from module.storage.assets import MATERIAL_ENTER, DISASSEMBLE_CANCEL, MATERIAL_CHECK, MATERIAL_STABLE_CHECK, \
    EQUIPMENT_ENTER, DISASSEMBLE, EQUIPMENT_FILTER, EQUIPMENT_FILTER_CONFIRM
from module.ui.assets import STORAGE_CHECK
from module.ui.page import page_storage
from module.ui.setting import Setting
from module.ui.ui import UI


class StorageUI(UI):
    @cached_property
    def storage_filter(self) -> Setting:
        delta = (147 + 1 / 3, 57)
        button_shape = (139, 42)
        setting = Setting(name='STORAGE', main=self)
        setting.add_setting(
            setting='rarity',
            option_buttons=ButtonGrid(
                origin=(219, 444), delta=delta, button_shape=button_shape, grid_shape=(7, 1), name='FILTER_RARITY'),
            option_names=['all', 'common', 'rare', 'elite', 'super_rare', 'ultra_rare', 'not_available'],
            option_default='all'
        )
        return setting

    def ui_goto_storage(self):
        return self.ui_ensure(destination=page_storage)

    def _wait_until_storage_stable(self):
        self.wait_until_stable(MATERIAL_STABLE_CHECK)
        self.handle_info_bar()

    def _storage_in_material(self, interval=0):
        """
        Args:
            interval (int): for appear func, varies
                            by needs/location

        Returns:
            bool, if in MATERIAL_CHECK, appear and match_appear_on
        """
        return self.match_template_color(MATERIAL_CHECK, offset=(20, 20), interval=interval)

    def _storage_enter_material(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_storage, any
            out: page_storage, material, MATERIAL_CHECK
        """
        logger.info('storage enter material')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._storage_in_material():
                break

            # disassemble -> equipment
            if self.appear_then_click(DISASSEMBLE_CANCEL, offset=(20, 20), interval=3):
                self.interval_reset(STORAGE_CHECK)
                continue
            # equipment -> material
            if self.appear(DISASSEMBLE, offset=(20, 20), interval=3):
                logger.info('DISASSEMBLE -> MATERIAL_ENTER')
                self.device.click(MATERIAL_ENTER)
                self.interval_reset(STORAGE_CHECK)
                continue
            # design -> material
            if self.appear(STORAGE_CHECK, offset=(20, 20), interval=3):
                logger.info('DISASSEMBLE -> MATERIAL_ENTER')
                self.device.click(MATERIAL_ENTER)
                continue

        self.interval_clear(STORAGE_CHECK)

    def _storage_enter_equipment(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_storage, any
            out: page_storage, equipment, DISASSEMBLE
        """
        logger.info('storage enter equipment')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(DISASSEMBLE, offset=(20, 20)):
                break

            # disassemble -> equipment
            if self.appear_then_click(DISASSEMBLE_CANCEL, offset=(20, 20), interval=3):
                self.interval_reset(STORAGE_CHECK)
                continue
            # material -> equipment
            if self._storage_in_material(interval=3):
                logger.info('_storage_in_material -> EQUIPMENT_ENTER')
                self.device.click(EQUIPMENT_ENTER)
                self.interval_reset(STORAGE_CHECK)
                continue
            # design -> equipment
            if self.appear(STORAGE_CHECK, offset=(20, 20), interval=3):
                logger.info('STORAGE_CHECK -> EQUIPMENT_ENTER')
                self.device.click(EQUIPMENT_ENTER)
                continue

        self.interval_clear(STORAGE_CHECK)

    def _storage_enter_disassemble(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_storage, any
            out: page_storage, disassemble, DISASSEMBLE_CANCEL
        """
        logger.info('storage enter disassemble')
        self.appear(STORAGE_CHECK, interval=3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(DISASSEMBLE_CANCEL, offset=(20, 20)):
                break

            # equipment -> disassemble
            if self.appear_then_click(DISASSEMBLE, offset=(20, 20), interval=3):
                self.interval_reset(STORAGE_CHECK)
                self.interval_reset(MATERIAL_CHECK)
                continue
            # material -> equipment
            if self._storage_in_material(interval=3):
                logger.info('_storage_in_material -> EQUIPMENT_ENTER')
                self.device.click(EQUIPMENT_ENTER)
                self.interval_reset(STORAGE_CHECK)
                continue
            # design -> equipment
            if self.appear(STORAGE_CHECK, offset=(20, 20), interval=3):
                logger.info('STORAGE_CHECK -> EQUIPMENT_ENTER')
                self.device.click(EQUIPMENT_ENTER)
                continue

        self.interval_clear(STORAGE_CHECK)

    def _equipment_filter_enter(self):
        self.interval_clear(EQUIPMENT_FILTER)
        self.ui_click(EQUIPMENT_FILTER, appear_button=STORAGE_CHECK, check_button=EQUIPMENT_FILTER_CONFIRM,
                      skip_first_screenshot=True)

    def _equipment_filter_confirm(self):
        self.interval_clear(EQUIPMENT_FILTER_CONFIRM)
        self.ui_click(EQUIPMENT_FILTER_CONFIRM, check_button=STORAGE_CHECK, skip_first_screenshot=True)
        self._wait_until_storage_stable()

    def equipment_filter_set(self, rarity='all'):
        """
        A faster filter set function.

        Args:
            rarity (str, int): ['all', 'common', 'rare', 'elite', 'super_rare', 'ultra_rare']
                Also allow: 1 for common, 2 for rare, 3 for elite, 4 for super_rare, 5 for ultra_rare

        Pages:
            in: DISASSEMBLE
        """
        rarity_convert = {
            '1': 'common',
            '2': 'rare',
            '3': 'elite',
            '4': 'super_rare',
            '5': 'ultra_rare',
        }
        rarity = rarity_convert.get(str(rarity), rarity)
        self._equipment_filter_enter()
        self.storage_filter.set(rarity=rarity)
        self._equipment_filter_confirm()
