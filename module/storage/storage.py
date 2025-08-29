import numpy as np

from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.base.utils import rgb2gray
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2
from module.exception import ScriptError
from module.logger import logger
from module.ocr.ocr import Digit
from module.retire.assets import EQUIP_CONFIRM, EQUIP_CONFIRM_2
from module.shop.assets import AMOUNT_MINUS, AMOUNT_PLUS
from module.statistics.item import ItemGrid
from module.storage.assets import *
from module.storage.ui import StorageUI
from module.ui.assets import BACK_ARROW, STORAGE_CHECK
from module.ui.scroll import Scroll

MATERIAL_SCROLL = Scroll(METERIAL_SCROLL, color=(247, 211, 66))

EQUIPMENT_GRIDS = ButtonGrid(origin=(140, 88), delta=(159, 178), button_shape=(124, 124),
                             grid_shape=(7, 3), name='EQUIPMENT')
EQUIPMENT_ITEMS = ItemGrid(EQUIPMENT_GRIDS, templates={}, amount_area=(90, 98, 123, 123))
OCR_DISASSEMBLE_COUNT = Digit(DISASSEMBLE_COUNT_OCR, letter=(235, 235, 235))


class StorageFull(Exception):
    pass


class StorageHandler(StorageUI):
    storage_has_boxes = True

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
        else:
            raise ScriptError(f'Unknown box template rarity: {rarity}')

    def _handle_use_box_amount(self, amount):
        """
        Returns:
            bool: if clicked

        Pages:
            in: SHOP_BUY_CONFIRM_AMOUNT
        """
        logger.info(f'Set box amount')

        # same code from shop clerk
        ocr = Digit(BOX_AMOUNT_OCR, letter=(239, 239, 239), name='OCR_SHOP_AMOUNT')
        index_offset = (40, 50)

        # wait until amount buttons appear
        timeout = Timer(1, count=3).start()
        for _ in self.loop():
            # In case either -/+ shift position, use
            # shipyard ocr trick to accurately parse
            if self.appear(AMOUNT_MINUS, offset=index_offset) and self.appear(AMOUNT_PLUS, offset=index_offset):
                break
            if timeout.reached():
                logger.warning('Wait AMOUNT_MINUS AMOUNT_PLUS timeout')
                break

        # wait until a normal number
        current = 0
        timeout = Timer(1, count=3).start()
        for _ in self.loop():
            current = ocr.ocr(self.device.image)
            if 1 <= current <= amount + 10:
                break
            if timeout.reached():
                logger.warning('Wait box amount timeout')
                break

        # set amount
        # a ui_ensure_index
        logger.info(f'Set box amount: {amount}')
        skip_first = True
        retry = Timer(1, count=2)
        for _ in self.loop():
            if skip_first:
                skip_first = False
            else:
                current = ocr.ocr(self.device.image)
            diff = amount - current
            if diff == 0:
                break

            if retry.reached():
                button = AMOUNT_PLUS if diff > 0 else AMOUNT_MINUS
                self.device.multi_click(button, n=abs(diff), interval=(0.1, 0.2))
                retry.reset()

        return True

    def _storage_use_one_box(self, button, amount=1):
        """
        Args:
            button (Button): Box
            amount (int):

        Returns:
            int: amount of box used, not accurate

        Raises:
            StorageFull:

        Pages:
            in: MATERIAL_CHECK
            out: MATERIAL_CHECK
        """
        logger.hr('Use one box')
        success = False
        used = 0
        self.interval_clear([
            MATERIAL_CHECK,
            BOX_USE,
            GET_ITEMS_1,
            GET_ITEMS_2,
            EQUIPMENT_FULL,
            BOX_AMOUNT_CONFIRM,
            EQUIP_CONFIRM,
            EQUIP_CONFIRM_2,
        ])

        for _ in self.loop():
            # End
            if success and self._storage_in_material() and not self.appear(EQUIP_CONFIRM_2, offset=(20, 20)):
                break

            # use
            if self._storage_in_material(interval=5):
                self.device.click(button)
                continue
            if self.appear_then_click(BOX_USE, offset=(-330, -20, 20, 20), interval=5):
                self.interval_reset(MATERIAL_CHECK)
                continue
            if self.appear(GET_ITEMS_1, offset=(5, 5), interval=5):
                logger.info(f'{GET_ITEMS_1} -> {MATERIAL_ENTER}')
                self.device.click(MATERIAL_ENTER)
                self.interval_reset(MATERIAL_CHECK)
                continue
            if self.appear(GET_ITEMS_2, offset=(5, 5), interval=5):
                logger.info(f'{GET_ITEMS_2} -> {MATERIAL_ENTER}')
                self.device.click(MATERIAL_ENTER)
                self.interval_reset(MATERIAL_CHECK)
                continue
            # use match_template_color on BOX_AMOUNT_CONFIRM
            # a long animation that opens a box, will be on the top of BOX_AMOUNT_CONFIRM
            if self.match_template_color(BOX_AMOUNT_CONFIRM, offset=(20, 20), interval=5):
                self._handle_use_box_amount(amount)
                self.device.click(BOX_AMOUNT_CONFIRM)
                self.interval_reset(BOX_AMOUNT_CONFIRM)
                used = amount
                continue
            if self.appear_then_click(EQUIP_CONFIRM, offset=(20, 20), interval=5):
                self.interval_reset(MATERIAL_CHECK)
                continue
            if self.appear_then_click(EQUIP_CONFIRM_2, offset=(20, 20), interval=5):
                # GET_ITEMS_* don't appear that fast
                self.interval_reset(MATERIAL_CHECK)
                self.interval_clear([GET_ITEMS_1, GET_ITEMS_2])
                # EQUIP_CONFIRM_2 -> GET_ITEMS -> _storage_in_material
                # mark EQUIP_CONFIRM_2 as the last
                success = True
                continue

            # Storage full
            if self.appear(EQUIPMENT_FULL, offset=(20, 20)):
                logger.info('Storage full')
                # Close popup
                self.ui_click(MATERIAL_ENTER, check_button=self._storage_in_material, appear_button=EQUIPMENT_FULL,
                              retry_wait=3, skip_first_screenshot=True)
                raise StorageFull

        logger.info(f'Used {used} box(es)')
        return used

    def _storage_use_box_in_page(self, rarity, amount, skip_first_screenshot=False):
        """
        Args:
            rarity (int):
            amount (int): Expected amount of boxes to use
            skip_first_screenshot:

        Returns:
            int: Actual amount of box used, not accurate

        Pages:
            in: MATERIAL_CHECK
            out: MATERIAL_CHECK
        """
        used = 0
        timeout = Timer(1.5, count=3).start()
        while 1:
            logger.attr('Used', f'{used}/{amount}')
            if used >= amount:
                logger.info('Reached target amount, stop')
                break
            if timeout.reached():
                logger.info('No more boxes on this page, stop')
                break

            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            image = rgb2gray(self.device.image)
            sim, box_button = self._storage_box_template(rarity).match_result(image)
            if sim > 0.9:
                used += self._storage_use_one_box(box_button, amount)
                continue
            else:
                logger.info('No boxes found')
                continue

        return used

    def _storage_use_box_execute(self, rarity=1, amount=10):
        """
        Args:
            rarity (int): 1/2/3 for T1/T2/T3
            amount (int): use how many boxes at most

        Returns:
            int: amount of box used, not accurate

        Raises:
            StorageFull: If storage full

        Pages:
            in: page_storage, material, MATERIAL_CHECK
            out: page_storage, material, MATERIAL_CHECK
        """
        logger.hr('Use Box', level=2)
        used = 0

        if MATERIAL_SCROLL.appear(main=self):
            if rarity == 1:
                # T1 boxes are always at the bottom
                MATERIAL_SCROLL.set_bottom(main=self)
            else:
                MATERIAL_SCROLL.set_top(main=self)

            while 1:
                logger.hr('Use boxes in page')
                used += self._storage_use_box_in_page(rarity=rarity, amount=max(amount - used, 0))
                if used >= amount:
                    break
                if MATERIAL_SCROLL.at_bottom(main=self):
                    logger.info('Scroll bar reached end, stop')
                    break
                MATERIAL_SCROLL.next_page(main=self)
        else:
            logger.hr('Use boxes in page')
            used += self._storage_use_box_in_page(rarity=rarity, amount=amount)

        return used

    def _storage_disassemble_equipment_execute_once(self, amount=40):
        """
        Returns:
            int: amount of equipments disassembled

        Pages:
            in: DISASSEMBLE_CANCEL
            out: DISASSEMBLE_CANCEL
        """
        success = False
        amount = min(amount, 40)
        self.interval_clear([
            DISASSEMBLE_CONFIRM,
            DISASSEMBLE_POPUP_CONFIRM,
            GET_ITEMS_1,
            GET_ITEMS_2,
            DISASSEMBLE_CANCEL,
        ])
        logger.info(f'Disassemble once, expected amount: {amount}')

        for _ in self.loop():
            if self.appear(GET_ITEMS_1, offset=(5, 5), interval=3):
                logger.info(f'{GET_ITEMS_1} -> {DISASSEMBLE_CONFIRM}')
                self.device.click(DISASSEMBLE_CONFIRM)
                continue
            if self.appear(GET_ITEMS_2, offset=(5, 5), interval=3):
                logger.info(f'{GET_ITEMS_2} -> {DISASSEMBLE_CONFIRM}')
                self.device.click(DISASSEMBLE_CONFIRM)
                continue
            if self.handle_info_bar():
                continue
            if self.appear(DISASSEMBLE_CANCEL, offset=(20, 20)):
                break
        self.interval_clear([
            GET_ITEMS_1,
            GET_ITEMS_2,
        ])
        self.wait_until_stable(MATERIAL_STABLE_CHECK)

        items = EQUIPMENT_ITEMS.predict(self.device.image, name=False, amount=True)
        if not len(items):
            logger.warning('No items in storage to disassemble')
            return 0
        cumsum = np.cumsum([item.amount for item in items])
        for item, total in zip(items, cumsum):
            if item.amount <= 0:
                continue
            self.device.click(item)
            self.device.click_record.pop()
            if total >= amount:
                amount = total
                break
        amount = min(cumsum[-1], amount)

        # Wait items being selected
        logger.info(f'Disassemble once, in_storage amount: {amount}')
        timeout = Timer(1, count=2).start()
        prev_disassemble = 0
        while 1:
            self.device.screenshot()
            disassembled = OCR_DISASSEMBLE_COUNT.ocr(self.device.image)
            if disassembled >= amount:
                logger.info('Disassemble amount reached expected amount')
                break
            if timeout.reached():
                logger.warning('Wait disassemble amount timeout')
                break
            if disassembled > prev_disassemble:
                prev_disassemble = disassembled
                timeout.reset()

        logger.info(f'Disassemble once, actual amount: {disassembled}')
        if disassembled <= 0:
            logger.warning('No items selected to disassemble')
            return 0

        skip_first_screenshot = True
        click_count = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if click_count >= 3:
                # Probably because no item is selected,
                # _storage_disassemble_equipment_execute() will retry selecting
                logger.warning('Failed to confirm disassemble after 3 trial')
                disassembled = 0
                break
            if success and self.appear(DISASSEMBLE_CANCEL, offset=(20, 20)):
                self.wait_until_stable(MATERIAL_STABLE_CHECK)
                break

            if self.appear_then_click(DISASSEMBLE_CONFIRM, offset=(20, 20), interval=5):
                click_count += 1
                continue
            if self.appear_then_click(DISASSEMBLE_POPUP_CONFIRM, offset=(-15, -5, 5, 70), interval=5):
                # since 2025.05.20 disassemble no longer shows GET_ITEMS
                success = True
                continue
            if self.handle_popup_confirm('DISASSEMBLE'):
                continue
            if self.appear(GET_ITEMS_1, offset=(5, 5), interval=3):
                logger.info(f'{GET_ITEMS_1} -> {DISASSEMBLE_CONFIRM}')
                self.device.click(DISASSEMBLE_CONFIRM)
                success = True
                continue
            if self.appear(GET_ITEMS_2, offset=(5, 5), interval=3):
                logger.info(f'{GET_ITEMS_2} -> {DISASSEMBLE_CONFIRM}')
                self.device.click(DISASSEMBLE_CONFIRM)
                success = True
                continue

        return disassembled

    def _storage_disassemble_equipment_execute(self, rarity=1, amount=40):
        """
        Args:
            rarity (int): 1 for common, 2 for rare, 3 for elite, 4 for super_rare, 5 for ultra_rare
            amount (int): Expected amount to disassemble.
                Actual amount >= expected

        Pages:
            in: page_storage, equipment, DISASSEMBLE
            out: page_storage, equipment, DISASSEMBLE

        Returns:
            int: Actual amount of equipments disassembled
        """
        disassembled = 0
        self.equipment_filter_set(rarity=rarity)
        if MATERIAL_SCROLL.appear(main=self):
            MATERIAL_SCROLL.set_top(main=self)

        while 1:
            logger.hr('Disassemble once')
            logger.attr('Disassembled', f'{disassembled}/{amount}')
            if self.appear(EQUIPMENT_EMPTY, offset=(20, 20)):
                logger.info('Equipment list empty, stop')
                break
            if disassembled >= amount:
                logger.info('Reached target amount, stop')
                break

            if amount - disassembled < 40:
                disassembled += self._storage_disassemble_equipment_execute_once(amount=amount - disassembled)
            else:
                disassembled += self._storage_disassemble_equipment_execute_once()

        self.equipment_filter_set()
        return disassembled

    def storage_disassemble_equipment(self, rarity=1, amount=15):
        """
        Disassemble target amount of equipment.
        If not having enough equipment, use boxes then disassemble.

        Args:
            rarity (int): 1 for common, 2 for rare, 3 for elite, 4 for super_rare
            amount (int): Expected amount to disassemble.
                Actual amount >= expected

        Returns:
            int: Actual amount of equipments disassembled

        Pages:
            in: Any
            out: page_storage, equipment, DISASSEMBLE
        """
        logger.hr('Disassemble Equipment', level=2)
        self.ui_goto_storage()
        # No need, equipping toggle does not effect disassemble
        # self.equipping_set()
        # Also no need to call _wait_until_storage_stable(), filter confirm will do that
        disassembled = 0
        while 1:
            logger.attr('Total_Disassemble', f'{disassembled}/{amount}')
            if disassembled >= amount:
                logger.info('Reached total target amount, stop')
                break

            self._storage_enter_material()
            try:
                boxes = self._storage_use_box_execute(rarity=rarity, amount=amount - disassembled)
                if boxes <= 0:
                    logger.warning('No more boxes to use, disassemble equipment end')
                    self.storage_has_boxes = False
                    break
                # since 2025.05.20, equipments in boxes get disassembled automatically
                disassembled += boxes
                # use bos success, check total again
                continue
            except StorageFull:
                pass
            # handle storage full
            self._storage_enter_disassemble()
            equip = self._storage_disassemble_equipment_execute(rarity=rarity, amount=amount)
            disassembled += equip
            if equip <= 0:
                logger.warning('StorageFull but unable to disassemble, '
                               'probably because storage is full of rare equipments or above, '
                               'disassemble equipment end')
                logger.warning('Please manually disassemble some equipments to free up storage')
                self.storage_has_boxes = False
                break

        return disassembled

    def storage_use_box(self, rarity=1, amount=40):
        """
        Disassemble target amount of equipment.
        If not having enough equipment, use boxes then disassemble.

        Args:
            rarity (int): 1 for common, 2 for rare, 3 for elite, 4 for super_rare
            amount (int): Expected amount to disassemble.
                Actual amount >= expected

        Returns:
            int: Actual amount of equipments disassembled

        Pages:
            in: Any
            out: page_storage, material, MATERIAL_CHECK
        """
        logger.hr('Use boxes', level=2)
        self.ui_goto_storage()
        self._storage_enter_material()
        self._wait_until_storage_stable()

        used = 0
        while 1:
            self._storage_enter_disassemble()
            self._storage_disassemble_equipment_execute(rarity=rarity, amount=amount)

            logger.attr('Total_Used', f'{used}/{amount}')
            if used >= amount:
                logger.info('Reached total target amount, stop')
                break

            boxes = 0
            try:
                self._storage_enter_material()
                boxes = self._storage_use_box_execute(rarity=rarity, amount=amount - used)
                used += boxes
                if boxes <= 0:
                    logger.warning('No more boxes to use, use boxes end')
                    self.storage_has_boxes = False
                    break
            except StorageFull:
                if boxes <= 0:
                    logger.warning('Unable to use boxes because storage full, '
                                   'probably because storage is full of rare equipments or above, '
                                   'use boxes end')
                    logger.warning('Please manually disassemble some equipments to free up storage')
                    self.storage_has_boxes = False
                    break

        return used

    def handle_storage_full(self, rarity=1, amount=40):
        """
        Args:
            rarity (int): 1 for common, 2 for rare, 3 for elite, 4 for super_rare
            amount (int): Expected amount to disassemble.
                Actual amount >= expected

        Returns:
            bool: If handled

        Pages:
            in: Any, if EQUIPMENT_FULL appears, handle it
            out: the page before handling storage popup
        """
        if not self.appear(EQUIPMENT_FULL, offset=(30, 30), interval=2):
            return False

        # EQUIPMENT_FULL
        logger.info('handle_storage_full')
        self.ui_click(EQUIPMENT_FULL, check_button=DISASSEMBLE_CANCEL, skip_first_screenshot=True, retry_wait=3)
        disassembled = self._storage_disassemble_equipment_execute(rarity=rarity, amount=amount)
        if disassembled <= 0:
            logger.warning('Storage full but unable to disassemble any equipment')

        # Quit
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(DISASSEMBLE_CANCEL, offset=(30, 30), interval=3):
                continue
            if self.appear(DISASSEMBLE, offset=(30, 30), interval=3):
                self.device.click(BACK_ARROW)
                continue

            # End
            if not self.appear(STORAGE_CHECK, offset=(30, 30)):
                break

        return True
