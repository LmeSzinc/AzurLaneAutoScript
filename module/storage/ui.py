from module.base.button import ButtonGrid
from module.logger import logger
from module.storage.assets import MATERIAL_ENTER, DISASSEMBLE_CANCEL, MATERIAL_CHECK, MATERIAL_STABLE_CHECK, \
    EQUIPMENT_ENTER, DISASSEMBLE, EQUIPMENT_FILTER, EQUIPMENT_FILTER_CONFIRM
from module.ui.assets import STORAGE_CHECK
from module.ui.page import page_storage
from module.ui.ui import UI

FILTER_RARITY_GRIDS = ButtonGrid(
    origin=(284, 446), delta=(158, 0), button_shape=(137, 38), grid_shape=(6, 1), name='FILTER_RARITY')
FILTER_RARITY_TYPES = [['all', 'common', 'rare', 'elite', 'super_rare', 'ultra_rare']]


class StorageUI(UI):
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
        return self.appear(MATERIAL_CHECK, offset=(20, 20), interval=interval) and \
               MATERIAL_CHECK.match_appear_on(self.device.image)

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
                self.device.click(MATERIAL_ENTER)
                self.interval_reset(STORAGE_CHECK)
                continue
            # design -> material
            if self.appear(STORAGE_CHECK, offset=(20, 20), interval=3):
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
                self.device.click(EQUIPMENT_ENTER)
                self.interval_reset(STORAGE_CHECK)
                continue
            # design -> equipment
            if self.appear(STORAGE_CHECK, offset=(20, 20), interval=3):
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
                self.device.click(EQUIPMENT_ENTER)
                self.interval_reset(STORAGE_CHECK)
                continue
            # design -> equipment
            if self.appear(STORAGE_CHECK, offset=(20, 20), interval=3):
                self.device.click(EQUIPMENT_ENTER)
                continue

        self.interval_clear(STORAGE_CHECK)

    def _equipment_filter_enter(self):
        self.interval_clear(EQUIPMENT_FILTER)
        self.ui_click(EQUIPMENT_FILTER, check_button=EQUIPMENT_FILTER_CONFIRM, skip_first_screenshot=True)

    def _equipment_filter_confirm(self):
        self.interval_clear(EQUIPMENT_FILTER_CONFIRM)
        self.ui_click(EQUIPMENT_FILTER_CONFIRM, check_button=STORAGE_CHECK, skip_first_screenshot=True)
        self._wait_until_storage_stable()

    def _equipment_filter_set_execute(self, rarity='all', skip_first_screenshot=True):
        """
        A faster filter set function.
        Imitate module.retire.dock.Dock.dock_filter_set_execute, not complete.

        Args:
            rarity (str, list):

        Returns:
            bool: If success.

        Pages:
            in: EQUIPMENT_FILTER_CONFIRM
        """
        # [[button_1, need_enable_1], ...]
        list_filter = []
        rarity = rarity if isinstance(rarity, list) else [rarity]
        for x, y, button in FILTER_RARITY_GRIDS.generate():
            name = FILTER_RARITY_TYPES[y][x]
            list_filter.append([button, name in rarity])

        for _ in range(5):
            logger.info(
                f'Setting equipment filter rarity={rarity}')
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            change_count = 0
            for button, enable in list_filter:
                active = self.image_color_count(button, color=(181, 142, 90), threshold=235, count=250)
                # or self.image_color_count(button, color=(74, 117, 189), threshold=235, count=250)
                if enable and not active:
                    self.device.click(button)
                    change_count += 1

            # End
            if change_count == 0:
                return True

        logger.warning('Failed to set all equipment filters after 5 trial, assuming current filters are correct.')
        return False

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
        self._equipment_filter_set_execute()  # Reset filter
        self._equipment_filter_set_execute(rarity=rarity)
        self._equipment_filter_confirm()
