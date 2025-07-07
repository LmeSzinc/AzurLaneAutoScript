from module.base.timer import Timer
from module.base.utils import rgb2gray
from module.daemon.daemon_base import DaemonBase
from module.logger import logger
from module.ocr.ocr import Digit
from module.shop.assets import AMOUNT_MAX, AMOUNT_MINUS, AMOUNT_PLUS
from module.storage.assets import *
from module.storage.storage import StorageHandler, MATERIAL_SCROLL

    
class StorageBox(DaemonBase, StorageHandler):
    BOX_DISASSEMBLE_DICT = {}

    def _check_box_amount(self, button):
        """
        Args:
            button (Button): Box

        Returns:
            int: amount of box
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

    def get_preserved_box_amount(self, rarity):
        preserve = self.BOX_DISASSEMBLE_DICT[rarity][1]
        logger.attr(f'T{rarity} box preserved amount', preserve)
        return preserve

    def _storage_use_multi_box(self, buttons, rarity, amount):
        """
        Args:
            buttons (list[Button]): list of Boxes
            rarity (int):
            amount (int): Expected amount of boxes to use

        Returns:
            int: amount of box used, not accurate

        Pages:
            in: MATERIAL_CHECK
            out: MATERIAL_CHECK
        """
        logger.hr('Use multi boxes')
        used = 0
        end = True
        for box_button in buttons:
            box_amount = self._check_box_amount(box_button)
            preserve = self.get_preserved_box_amount(rarity)
            if box_amount <= preserve:
                self.ui_click(MATERIAL_ENTER, check_button=self._storage_in_material, appear_button=BOX_USE, 
                              offset=(-330, -20, 20, 20), retry_wait=3, skip_first_screenshot=True)
                continue
            end = False
            used += self._storage_use_one_box(box_button, min(box_amount - preserve, 100))
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
                box_used = self._storage_use_multi_box(box_buttons, rarity, amount)
                # End
                if box_used == -1:
                    used = 0
                    break
                used += box_used
                continue
            else:
                logger.info('No boxes found')
                continue

        return used

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
                if amount >= 100:
                    self.device.click(AMOUNT_MAX)
                else:
                    button = AMOUNT_PLUS if diff > 0 else AMOUNT_MINUS
                    self.device.multi_click(button, n=abs(diff), interval=(0.1, 0.2))
                retry.reset()

        return True

    def get_box_disassemble_config(self):
        self.BOX_DISASSEMBLE_DICT[3] = [self.config.BoxDisassemble_UsePurpleBox, self.config.BoxDisassemble_PurpleBoxLimit]
        self.BOX_DISASSEMBLE_DICT[2] = [self.config.BoxDisassemble_UseBlueBox, self.config.BoxDisassemble_BlueBoxLimit]
        self.BOX_DISASSEMBLE_DICT[1] = [self.config.BoxDisassemble_UseWhiteBox, self.config.BoxDisassemble_WhiteBoxLimit]

    def box_disassemble(self):
        logger.hr('Box disassemble', level=1)
        self.get_box_disassemble_config()
        for rarity, box_info in self.BOX_DISASSEMBLE_DICT.items():
            if not box_info[0]:
                continue
            logger.hr(f'Disassemble T{rarity} box', level=2)
            self.storage_disassemble_equipment(rarity=rarity, amount=1000000)
            self.ui_goto_main()

    def run(self):
        self.box_disassemble()


if __name__ == '__main__':
    self = StorageBox(config='alas')
    self.run()
