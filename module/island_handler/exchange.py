from module.island_handler.shop_ui import IslandShopUI
from module.island_handler.assets import *
from module.logger import logger
from module.ocr.ocr import Digit


class IslandExchange(IslandShopUI):
    def exchange_fish_meat(self, delta_count):
        ocr = Digit(ISLAND_EXCHANGE_TOTAL_AMOUNT, lang='cnocr', letter=(60, 60, 60), threshold=160)
        before_amount = None
        for _ in self.loop(timeout=3):
            before_amount = ocr.ocr(self.device.image)
            if before_amount is not None:
                break
        else:
            logger.warning('Unable to read fish amount before exchange')
            return False
        for _ in self.loop(timeout=3):
            if self.handle_island_additional():
                continue
            if self.image_color_count(ISLAND_EXCHANGE_SELECT_ALL, color=(255, 255, 255), count=25):
                break
            if self.appear_then_click(ISLAND_EXCHANGE_SELECT_ALL, offset=(20, 20), interval=1):
                continue
        else:
            logger.warning('No fish available for exchange')
            return False
        for _ in self.loop():
            if self.handle_island_additional():
                continue
            if self.handle_island_popup_confirm('EXCHANGE'):
                continue
            if self.appear(ISLAND_EXCHANGE_SELECT_ALL, offset=(20, 20)):
                break
            if self.appear_then_click(ISLAND_EXCHANGE_CONFIRM, offset=(20, 20), interval=1):
                continue
        after_amount = before_amount
        exchanged_amount = 0
        for _ in self.loop(timeout=3):
            if self.handle_island_additional():
                continue
            after_amount = ocr.ocr(self.device.image)
            if after_amount is None:
                continue
            exchanged_amount = after_amount - before_amount
            if exchanged_amount >= delta_count:
                return True
        else:
            logger.warning(
                f'Exchange failed, expected {delta_count}, '
                f'but got {exchanged_amount} ({before_amount} -> {after_amount})'
            )
            return False

    def island_shop_exchange(self, require_dict={}):
        success = True
        if 2521 in require_dict.keys():
            # 2521 means Freshwater Fish Meat
            self.island_shop_side_navbar_ensure(main_index=6, sub_index=0)
            success = self.exchange_fish_meat(delta_count=require_dict[2521]) and success
        if 2522 in require_dict.keys():
            # 2522 means Saltwater Fish Meat
            self.island_shop_side_navbar_ensure(main_index=6, sub_index=1)
            success = self.exchange_fish_meat(delta_count=require_dict[2522]) and success
        return success

    def island_shop_exchange_all_fish_meat(self):
        """Exchange all available freshwater and saltwater fish in one visit."""
        return self.island_shop_exchange({2521: 0, 2522: 0})
