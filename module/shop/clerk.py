import cv2

from module.base.timer import Timer
from module.exception import ScriptError
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from module.retire.retirement import Retirement
from module.shop.assets import *
from module.shop.base import ShopBase
from module.shop.shop_select_globals import *
from module.ui.assets import BACK_ARROW


class StockCounter(DigitCounter):
    def pre_process(self, image):
        # Convert to gray scale
        r, g, b = cv2.split(image)
        image = cv2.max(cv2.max(r, g), b)

        return 255 - image


SHOP_SELECT_PR = [SHOP_SELECT_PR1, SHOP_SELECT_PR2, SHOP_SELECT_PR3]
OCR_SHOP_SELECT_STOCK = StockCounter(SHOP_SELECT_STOCK)

OCR_SHOP_AMOUNT = Digit(SHOP_AMOUNT, letter=(239, 239, 239), name='OCR_SHOP_AMOUNT')


class ShopClerk(ShopBase, Retirement):
    def shop_get_choice(self, item):
        """
        Gets the configuration saved in
        for the appropriate variant shop
        i.e. GuildShop_X

        Args:
            item (Item):

        Returns:
            str

        Raises:
            ScriptError
        """
        group = item.group
        if group == 'pr':
            postfix = None
            for _ in range(3):
                if _:
                    self.device.sleep((0.3, 0.5))
                    self.device.screenshot()

                for idx, btn in enumerate(SHOP_SELECT_PR):
                    if self.appear(btn, offset=(20, 20)):
                        postfix = f'{idx + 1}'
                        break

                if postfix is not None:
                    break
                logger.warning('Failed to detect PR series, '
                               'app may be lagging or frozen')
        else:
            postfix = f'_{item.tier.upper()}'

        ugroup = group.upper()
        class_name = self.__class__.__name__
        try:
            return getattr(self.config, f'{class_name}_{ugroup}{postfix}')
        except Exception:
            logger.critical(f'No configuration with name '
                            f'\'{class_name}_{ugroup}{postfix}\'')
            raise ScriptError

    def shop_get_select(self, item):
        """
        Gets the appropriate select
        grid button

        Args:
            item (Item):

        Returns:
            Button

        Raises:
            ScriptError
        """
        # Item group must belong in SELECT_ITEM_INFO_MAP
        group = item.group
        if group not in SELECT_ITEM_INFO_MAP:
            logger.critical(f'Unexpected item group \'{group}\'; '
                            f'expected one of {SELECT_ITEM_INFO_MAP.keys()}')
            raise ScriptError

        # Get configured choice for item
        choice = self.shop_get_choice(item)

        # Get appropriate select button for click
        try:
            item_info = SELECT_ITEM_INFO_MAP[group]
            index = item_info['choices'][choice]
            if group == 'pr':
                for idx, btn in enumerate(SHOP_SELECT_PR):
                    if self.appear(btn, offset=(20, 20)):
                        series_key = f's{idx + 1}'
                        return item_info['grid'][series_key].buttons[index]
            else:
                return item_info['grid'].buttons[index]
        except Exception:
            logger.critical(f'SELECT_ITEM_INFO_MAP may be malformed; '
                            f'item group \'{group}\' entry is compromised')
            raise ScriptError

    def shop_buy_select_execute(self, item):
        """
        Args:
            item (Item):

        Returns:
            bool:
        """
        # Search for appropriate select grid button for item
        select = self.shop_get_select(item)

        # Get displayed stock limit; varies between shops
        # If read 0, then warn and exit as cannot safely buy
        _, _, limit = OCR_SHOP_SELECT_STOCK.ocr(self.device.image)
        if not limit:
            logger.critical(f'{item.name}\'s stock count cannot be '
                            'extracted. Advised to re-cut the asset '
                            'OCR_SHOP_SELECT_STOCK')
            raise ScriptError

        # Click in intervals until plus/minus are onscreen
        click_timer = Timer(3, count=6)
        select_offset = (500, 400)
        while 1:
            if click_timer.reached():
                self.device.click(select)
                click_timer.reset()

            # Scan for plus/minus locations; searching within
            # offset will update the click position automatically
            self.device.screenshot()
            if self.appear(SELECT_MINUS, offset=select_offset) and self.appear(SELECT_PLUS, offset=select_offset):
                break
            else:
                continue

        # Total number to purchase altogether
        total = int(self._currency // item.price)
        diff = limit - total
        if diff > 0:
            limit = total

        # Alias OCR_SHOP_SELECT_STOCK to adapt with
        # ui_ensure_index; prevent overbuying when
        # out of stock; item.price may still evaluate
        # incorrectly
        def shop_buy_select_ensure_index(image):
            current, remain, _ = OCR_SHOP_SELECT_STOCK.ocr(image)
            if not current:
                group_case = item.group.title() if len(item.group) > 2 else item.group.upper()
                logger.info(f'{group_case}(s) out of stock; exit to prevent overbuying')
                return limit
            return remain

        self.ui_ensure_index(limit, letter=shop_buy_select_ensure_index, prev_button=SELECT_MINUS,
                             next_button=SELECT_PLUS,
                             skip_first_screenshot=True)
        self.device.click(SHOP_BUY_CONFIRM_SELECT)
        return True

    def shop_buy_amount_execute(self, item):
        """
        Args:
            item (Item):

        Returns:
            bool:

        Raises:
            ScriptError
        """
        index_offset = (40, 20)

        # In case either -/+ shift position, use
        # shipyard ocr trick to accurately parse
        self.appear(AMOUNT_MINUS, offset=index_offset)
        self.appear(AMOUNT_PLUS, offset=index_offset)
        area = OCR_SHOP_AMOUNT.buttons[0]
        OCR_SHOP_AMOUNT.buttons = [(AMOUNT_MINUS.button[2] + 3, area[1], AMOUNT_PLUS.button[0] - 3, area[3])]

        # Total number that can be purchased
        # altogether based on clicking max
        # Needs small delay for stable image
        self.appear_then_click(AMOUNT_MAX, offset=(50, 50))
        self.device.sleep((0.3, 0.5))
        self.device.screenshot()
        limit = OCR_SHOP_AMOUNT.ocr(self.device.image)
        if not limit:
            logger.critical('OCR_SHOP_AMOUNT resulted in zero (0); '
                            'asset may be compromised')
            raise ScriptError

        # Adjust purchase amount if needed
        total = int(self._currency // item.price)
        diff = limit - total
        if diff > 0:
            limit = total

        self.ui_ensure_index(limit, letter=OCR_SHOP_AMOUNT, prev_button=AMOUNT_MINUS, next_button=AMOUNT_PLUS,
                             skip_first_screenshot=True)
        self.device.click(SHOP_BUY_CONFIRM_AMOUNT)
        return True

    def shop_interval_clear(self):
        """
        Override in variant class
        if need to clear particular
        asset intervals
        """
        self.interval_clear(BACK_ARROW)
        self.interval_clear(SHOP_BUY_CONFIRM)

    def shop_buy_handle(self, item):
        """
        Override in variant class
        for specific buy handle
        actions

        Args:
            item (Item):

        Returns:
            bool:
        """
        return False

    def shop_buy_execute(self, item, skip_first_screenshot=True):
        """
        Args:
            item: Item to check
            skip_first_screenshot: bool

        Returns:
            None: exits appropriately therefore successful
        """
        success = False
        self.shop_interval_clear()

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(BACK_ARROW, offset=(20, 20), interval=3):
                self.device.click(item)
                continue
            if self.appear_then_click(SHOP_BUY_CONFIRM, offset=(20, 20), interval=3):
                self.interval_reset(BACK_ARROW)
                continue
            if self.shop_buy_handle(item):
                self.interval_reset(BACK_ARROW)
                continue
            if self.handle_retirement():
                self.interval_reset(BACK_ARROW)
                continue
            if self.handle_info_bar():
                self.interval_reset(BACK_ARROW)
                success = True
                continue
            if self.shop_obstruct_handle():
                self.interval_reset(BACK_ARROW)
                success = True
                continue

            # End
            if success and self.appear(BACK_ARROW, offset=(20, 20)):
                break

    def shop_buy(self):
        """
        Returns:
            bool: If success, and able to continue.
        """
        for _ in range(12):
            logger.hr('Shop buy', level=2)
            # Get first for innate delay to ocr
            # shop currency for accurate parse
            items = self.shop_get_items()
            self.shop_currency()
            if self._currency <= 0:
                logger.warning(f'Current funds: {self._currency}, stopped')
                return False

            item = self.shop_get_item_to_buy(items)
            if item is None:
                logger.info('Shop buy finished')
                return True
            else:
                self.shop_buy_execute(item)
                continue

        logger.warning('Too many items to buy, stopped')
        return True
