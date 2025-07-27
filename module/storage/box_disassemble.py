from module.base.timer import Timer
from module.base.utils import rgb2gray
from module.logger import logger
from module.ocr.ocr import Digit
from module.shop.assets import AMOUNT_MAX, AMOUNT_MINUS, AMOUNT_PLUS
from module.storage.assets import *
from module.storage.storage import StorageHandler

BOX_DISASSEMBLE_DICT = {
    3: 'Purple',
    2: 'Blue',
    1: 'White',
}


class StorageBox(StorageHandler):
    box_preserve_amount = 2000
    BOX_MAX_USE_AMOUNT = 100

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
            if self.appear(AMOUNT_MINUS, offset=index_offset) and self.appear(AMOUNT_PLUS, offset=index_offset) and \
                    self.appear(AMOUNT_MAX, offset=index_offset):
                break
            if timeout.reached():
                logger.warning('Wait AMOUNT_MINUS AMOUNT_PLUS AMOUNT_MAX timeout')
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
                if amount > self.BOX_MAX_USE_AMOUNT // 2 and abs(diff) >= self.BOX_MAX_USE_AMOUNT // 2:
                    self.device.click(AMOUNT_MAX)
                else:
                    button = AMOUNT_PLUS if diff > 0 else AMOUNT_MINUS
                    self.device.multi_click(button, n=abs(diff), interval=(0.1, 0.2))
                retry.reset()

        return True

    def _check_box_amount(self, button):
        """
        Args:
            button (Button): Box

        Returns:
            int: amount of box

        Pages:
            in: MATERIAL_CHECK
            out: BOX_USE
        """
        logger.hr('Check box amount')
        amount = 0
        ocr = Digit(BOX_REMAIN_AMOUNT_OCR, letter=(229, 227, 3), name='OCR_BOX_REAMIN_AMOUNT')
        self.interval_clear(MATERIAL_CHECK)
        for _ in self.loop():
            if self._storage_in_material(interval=5):
                self.device.click(button)
                continue
            if self.appear(BOX_USE, offset=(-330, -20, 20, 20)):
                break

        timeout = Timer(1, count=3).start() 
        for _ in self.loop():
            amount = ocr.ocr(self.device.image)
            if amount > 0:
                break
            if timeout.reached():
                logger.warning('Wait check box amount timeout')
                break
        return amount

    def _storage_use_multi_box(self, buttons):
        """
        Args:
            buttons (list[Button]): list of Boxes

        Returns:
            int: amount of box used, not accurate.
                 -1 means the end of box disassemble

        Pages:
            in: MATERIAL_CHECK
            out: MATERIAL_CHECK
        """
        logger.hr('Use multi boxes')
        used = 0
        end = True
        for box_button in buttons:
            box_amount = self._check_box_amount(box_button)
            preserve = self.box_preserve_amount
            if box_amount <= preserve:
                self.ui_click(MATERIAL_ENTER, check_button=self._storage_in_material, appear_button=BOX_USE, 
                              offset=(-330, -20, 20, 20), retry_wait=3, skip_first_screenshot=True)
                self.device.click_record_clear()
                continue
            end = False
            used += self._storage_use_one_box(box_button, amount=min(box_amount - preserve, 100))
        if end:
            return -1
        return used

    def _storage_use_box_in_page(self, rarity, amount, skip_first_screenshot=False):
        """
        Args:
            rarity (int):
            amount (int): Expected amount of boxes to use
            skip_first_screenshot:

        Returns:
            int: Actual amount of box used, not accurate
                 -1 means the end of box disassemble

        Pages:
            in: MATERIAL_CHECK
            out: MATERIAL_CHECK
        """
        used = 0
        timeout = Timer(1.5, count=3).start()
        while 1:
            logger.attr('Used', f'{used}')
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
            box_buttons = self._storage_box_template(rarity).match_multi(image, similarity=0.9)
            if box_buttons:
                box_used = self._storage_use_multi_box(box_buttons)
                # End
                if box_used == -1:
                    used = 0
                    break
                used += box_used
                timeout.reset()
                continue
            else:
                logger.info('No boxes found')
                continue

        return used

    def box_disassemble(self, rarity=1, preserve=2000):
        """
        Disassemble target rarity boxes.

        Args:
            rarity (int): 1 for common, 2 for rare, 3 for elite, 4 for super_rare
            preserve (int): Expected amount of boxes to preserve

        Pages:
            in: Any
            out: page_main
        """
        logger.hr(f'Disassemble T{rarity} box', level=2)
        self.box_preserve_amount = preserve
        self.storage_disassemble_equipment(rarity=rarity, amount=1000000)
        self.ui_goto_main()

    def run(self):
        """
        Pages:
            in: Any page
            out: page_main
        """
        logger.hr('Box disassemble', level=1)
        for rarity, box_color in BOX_DISASSEMBLE_DICT.items():
            if self.config.__getattribute__(f'BoxDisassemble_Use{box_color}Box'):
                self.box_disassemble(
                    rarity=rarity,
                    preserve=self.config.__getattribute__(f'BoxDisassemble_{box_color}BoxLimit')
                )


if __name__ == '__main__':
    self = StorageBox(config='alas')
    self.run()
