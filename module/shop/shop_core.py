from module.base.decorator import cached_property
from module.exception import ScriptError
from module.logger import logger
from module.ocr.ocr import Digit
from module.shop.assets import *
from module.shop.base import ShopBase, ShopItemGrid

OCR_SHOP_CORE = Digit(SHOP_CORE, letter=(239, 239, 239), name="OCR_SHOP_CORE")
OCR_SHOP_AMOUNT = Digit(SHOP_AMOUNT, letter=(239, 239, 239), name="OCR_SHOP_AMOUNT")


class CoreShop(ShopBase):
    _shop_core = 0

    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        return self.config.CoreShop_Filter.strip()

    @cached_property
    def shop_core_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_core_items = ShopItemGrid(
            shop_grid, templates={}, amount_area=(60, 74, 96, 95)
        )
        shop_core_items.load_template_folder("./assets/shop/core")
        shop_core_items.load_cost_template_folder("./assets/shop/cost")
        return shop_core_items

    def shop_items(self):
        """
        Shared alias for all shops
        If there are server-lang
        differences, reference
        shop_guild/medal for @Config
        example

        Returns:
            ShopItemGrid:
        """
        return self.shop_core_items

    def shop_currency(self):
        """
        Ocr shop core currency

        Returns
            int: core amount
        """
        self._shop_core = OCR_SHOP_CORE.ocr(self.device.image)
        logger.info(f"Core: {self._shop_core}")
        return self._shop_core

    def shop_check_item(self, item):
        """
        Args:
            item: Item to check

        Returns:
            bool:
        """
        if item.price > self._shop_core:
            return False
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
        OCR_SHOP_AMOUNT.buttons = [
            (AMOUNT_MINUS.button[2] + 3, area[1], AMOUNT_PLUS.button[0] - 3, area[3])
        ]

        # Total number that can be purchased
        # altogether based on clicking max
        # Needs small delay for stable image
        self.appear_then_click(AMOUNT_MAX, offset=(50, 50))
        self.device.sleep((0.3, 0.5))
        self.device.screenshot()
        limit = OCR_SHOP_AMOUNT.ocr(self.device.image)
        if not limit:
            logger.critical(
                "OCR_SHOP_AMOUNT resulted in zero (0); " "asset may be compromised"
            )
            raise ScriptError

        # Adjust purchase amount if needed
        total = int(self._shop_core // item.price)
        diff = limit - total
        if diff > 0:
            limit = total

        self.ui_ensure_index(
            limit,
            letter=OCR_SHOP_AMOUNT,
            prev_button=AMOUNT_MINUS,
            next_button=AMOUNT_PLUS,
            skip_first_screenshot=True,
        )
        self.device.click(SHOP_BUY_CONFIRM_AMOUNT)
        return True

    def shop_interval_clear(self):
        """
        Clear interval on select assets for
        shop_core_buy_handle
        """
        super().shop_interval_clear()
        self.interval_clear(SHOP_BUY_CONFIRM_AMOUNT)

    def shop_buy_handle(self, item):
        """
        Handle shop_core buy interface if detected

        Args:
            item: Item to handle

        Returns:
            bool: whether interface was detected and handled
        """
        if self.appear(SHOP_BUY_CONFIRM_AMOUNT, offset=(20, 20), interval=3):
            self.shop_buy_amount_execute(item)
            self.interval_reset(SHOP_BUY_CONFIRM_AMOUNT)
            return True

        return False

    def run(self):
        """
        Run Core Shop
        """
        # Base case; exit run if filter empty
        if not self.shop_filter:
            return

        # When called, expected to be in
        # correct Core Shop interface
        logger.hr("Core Shop", level=1)

        # Execute buy operations
        self.shop_buy()
