from module.base.button import ButtonGrid
from module.base.utils import rgb2gray
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2
from module.logger import logger
from module.storage.assets import *
from module.storage.ui import StorageUI
from module.ui.scroll import Scroll

MATERIAL_SCROLL = Scroll(METERIAL_SCROLL, color=(247, 211, 66))

EQUIPMENT_GRIDS = ButtonGrid(origin=(172, 117), delta=(159, 178), button_shape=(60, 60),
                             grid_shape=(7, 3), name='EQUIPMENT')


class StorageFull(Exception):
    pass


class StorageHandler(StorageUI):
    @staticmethod
    def _storage_box_template(rarity):
        if rarity == 1:
            return TEMPLATE_BOX_T1
        if rarity == 2:
            return TEMPLATE_BOX_T2
        if rarity == 3:
            return TEMPLATE_BOX_T3
        if rarity == 4:
            return TEMPLATE_BOX_T4

    def _storage_use_one_box(self, button, skip_first_screenshot=True):
        """
        Args:
            button (Button): Box
            skip_first_screenshot (bool):

        Returns:
            int: amount of box used, not accurate

        Pages:
            in: MATERIAL_CHECK
            out: MATERIAL_CHECK
        """
        success = False
        used = 0
        for b in [MATERIAL_CHECK, BOX_USE_ONE, BOX_USE_TEN, GET_ITEMS_1, GET_ITEMS_2]:
            self.interval_clear(b)

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(MATERIAL_CHECK, offset=(20, 20), interval=5):
                self.device.click(button)
                continue
            if self.appear(BOX_USE_TEN, offset=(-80, -5, 10, 5), interval=5):
                used = 10
                self.device.click(BOX_USE_TEN)
                self.interval_reset(MATERIAL_CHECK)
                continue
            if self.appear_then_click(BOX_USE_ONE, offset=(-150, -5, 10, 5), interval=5):
                used = 1
                self.interval_reset(MATERIAL_CHECK)
                continue
            if self.appear_then_click(GET_ITEMS_1, interval=5):
                self.interval_reset(MATERIAL_CHECK)
                success = True
                continue
            if self.appear_then_click(GET_ITEMS_2, offset=(5, 5), interval=5):
                self.interval_reset(MATERIAL_CHECK)
                success = True
                continue

            # Storage full
            if self.appear_then_click(EQUIPMENT_FULL, offset=(20, 20)):
                raise StorageFull
            # End
            if success and self.appear(MATERIAL_CHECK, offset=(20, 20)):
                break
        return used

    def _storage_use_box_in_page(self, rarity, amount, skip_first_screenshot=False):
        """

        Args:
            rarity (int):
            amount (int):
            skip_first_screenshot:

        Returns:
            int: amount of box used, not accurate

        Pages:
            in: MATERIAL_CHECK
            out: MATERIAL_CHECK
        """
        used = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            image = rgb2gray(self.device.image)
            sim, box_button = self._storage_box_template(rarity).match_result(image)
            logger.warning(sim)
            if sim > 0.9 and amount > used:
                used += self._storage_use_one_box(box_button)
                continue
            else:
                break
        return used

    def storage_use_box(self, rarity, amount):
        """

        Args:
            rarity (int): 1/2/3 for T1/T2/T3
            amount (int): use how many boxs at most

        Returns:
            int: amount of box used, not accurate

        Raises:
            StorageFull: If storage full

        """
        logger.hr('Use Box', level=2)
        self.ui_goto_storage()
        self.material_enter()
        used = 0
        try:
            if MATERIAL_SCROLL.appear(main=self):
                MATERIAL_SCROLL.set_top(main=self)

                while amount > used:
                    used += self._storage_use_box_in_page(rarity=rarity, amount=amount - used)
                    if MATERIAL_SCROLL.at_bottom(main=self):
                        break
                    MATERIAL_SCROLL.next_page(main=self)
            else:
                used += self._storage_use_box_in_page(rarity=rarity, amount=amount)
        except StorageFull:
            logger.info('Storage full')
            raise StorageFull
        return used

    def _storage_disassemble_equipment_execute_once(self):
        """
        Returns:
            bool: If success

        Pages:
            in: DISASSEMBLE_CANCEL
            out: DISASSEMBLE_CANCEL
        """
        success = False
        for button in [DISASSEMBLE_CONFIRM, DISASSEMBLE_POPUP_CONFIRM, GET_ITEMS_CONTINUE, DISASSEMBLE_CANCEL]:
            self.interval_clear(button)

        self.handle_info_bar()
        for _, _, button in EQUIPMENT_GRIDS.generate():
            self.device.click(button)

        while 1:
            self.device.screenshot()
            if self.appear_then_click(DISASSEMBLE_CONFIRM, offset=(20, 20), interval=5):
                continue
            if self.appear_then_click(DISASSEMBLE_POPUP_CONFIRM, offset=(20, 20), interval=5):
                continue
            if self.handle_popup_confirm():
                continue
            if self.appear_then_click(GET_ITEMS_CONTINUE):
                success = True
                continue

            if success and self.appear(DISASSEMBLE_CANCEL, offset=(20, 20)):
                self.wait_until_stable(MATERIAL_STABLE_CHECK)
                break

    def _storage_disassemble_equipment_execute(self, rarity):
        """

        Args:
            rarity:

        Pages:
            in: DISASSEMBLE
            out: DISASSEMBLE

        """
        self.ui_click(click_button=DISASSEMBLE, check_button=DISASSEMBLE_CANCEL, skip_first_screenshot=True)
        self.equipment_filter_set(rarity=rarity)
        while not self.appear(EQUIPMENT_EMPTY, offset=(20, 20)):
            self._storage_disassemble_equipment_execute_once()
        self.equipment_filter_set()
        self.ui_click(click_button=DISASSEMBLE_CANCEL, check_button=DISASSEMBLE, skip_first_screenshot=True)

    def storage_disassemble_equipment(self, rarity='common'):
        logger.hr('Disassemble Equipment', level=2)
        self.ui_goto_storage()
        self.equipment_enter()
        self.equipping_set()
        self._storage_disassemble_equipment_execute(rarity=rarity)


if __name__ == '__main__':
    a = StorageHandler('alas')
    while 1:
        try:
            s = a.storage_use_box(rarity=4, amount=30)
            if s == 0:
                break
        except StorageFull:
            a.storage_disassemble_equipment()
