from module.base.button import ButtonGrid
from module.equipment.equipment import equipping_filter
from module.logger import logger
from module.storage.assets import MATERIAL_ENTER, DISASSEMBLE_CANCEL, MATERIAL_CHECK, MATERIAL_STABLE_CHECK, \
    EQUIPMENT_ENTER, DISASSEMBLE, EQUIPMENT_FILTER, EQUIPMENT_FILTER_CONFIRM
from module.ui.assets import STORAGE_CHECK
from module.ui.page import page_storage
from module.ui.ui import UI

FILTER_RARITY_GRIDS = ButtonGrid(
    origin=(284, 446), delta=(158, 0), button_shape=(137, 38), grid_shape=(6, 1), name='FILTER_RARITY')
FILTER_RARITY_TYPES = [['all', 'common', 'rare', 'elite', 'super_rare', 'ultra']]


class StorageUI(UI):
    def ui_goto_storage(self):
        return self.ui_ensure(destination=page_storage)

    def material_enter(self):
        """
        Pages:
            in: page_storage
            out: MATERIAL_CHECK
        """
        # May enter DISASSEMBLE in accident
        while 1:
            if self.appear(MATERIAL_ENTER, offset=(20, 20)):
                break
            if self.appear_then_click(DISASSEMBLE_CANCEL, offset=(20, 20), interval=5):
                continue
        self.ui_click(MATERIAL_ENTER, check_button=MATERIAL_CHECK,
                      retry_wait=3, offset=(20, 20), skip_first_screenshot=True)
        self.handle_info_bar()
        self.wait_until_stable(MATERIAL_STABLE_CHECK)

    def equipment_enter(self):
        """
        Pages:
            in: page_storage
            out: DISASSEMBLE (equipment)
        """
        self.ui_click(EQUIPMENT_ENTER, check_button=DISASSEMBLE,
                      retry_wait=3, offset=(20, 20), skip_first_screenshot=True)
        self.handle_info_bar()
        self.wait_until_stable(MATERIAL_STABLE_CHECK)

    def _equipment_filter_enter(self):
        self.ui_click(EQUIPMENT_FILTER, check_button=EQUIPMENT_FILTER_CONFIRM, skip_first_screenshot=True)

    def _equipment_filter_confirm(self):
        self.ui_click(EQUIPMENT_FILTER_CONFIRM, check_button=STORAGE_CHECK, skip_first_screenshot=True)
        self.wait_until_stable(MATERIAL_STABLE_CHECK)

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
                    self.device.sleep((0.1, 0.2))
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
            rarity (str, ): ['all', 'common', 'rare', 'elite', 'super_rare', 'ultra']

        Pages:
            in: DISASSEMBLE
        """
        self._equipment_filter_enter()
        self._equipment_filter_set_execute()  # Reset filter
        self._equipment_filter_set_execute(rarity=rarity)
        self._equipment_filter_confirm()

    def equipping_set(self, enable=False):
        if equipping_filter.set('on' if enable else 'off', main=self):
            self.wait_until_stable(MATERIAL_STABLE_CHECK)
