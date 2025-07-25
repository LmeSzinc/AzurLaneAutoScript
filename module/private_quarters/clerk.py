from module.base.timer import Timer
from module.logger import logger
from module.private_quarters.assets import *
from module.private_quarters.ui import PQShopUI
from module.shop.clerk import ShopClerk


class PQShopClerk(ShopClerk, PQShopUI):
    def shop_interval_clear(self):
        """
        Override in variant class
        if need to clear particular
        asset intervals
        """
        self.interval_clear([
            PRIVATE_QUARTERS_SHOP_CHECK,
            PRIVATE_QUARTERS_SHOP_AMOUNT_MAX,
            PRIVATE_QUARTERS_SHOP_CONFIRM_AMOUNT
        ])

    def shop_buy_execute(self, item, skip_first_screenshot=True):
        """
        Args:
            item: Item to check
            skip_first_screenshot: bool

        Returns:
            None: exits appropriately therefore successful
        """

        # Helper funcs to ensure the appearance for pre and post
        # conditions for after confirm of purchase
        def after_confirm_state():
            return (self.appear(PRIVATE_QUARTERS_SHOP_WEEKLY_ROSES_GET, offset=(20, 20)) or
                    self.appear(PRIVATE_QUARTERS_SHOP_WEEKLY_CAKES_GET, offset=(20, 20)))

        def after_purchase_state():
            return (not self.appear(PRIVATE_QUARTERS_SHOP_WEEKLY_ROSES_GET, offset=(20, 20)) and
                    not self.appear(PRIVATE_QUARTERS_SHOP_WEEKLY_CAKES_GET, offset=(20, 20)) and
                    self.appear(PRIVATE_QUARTERS_SHOP_CHECK))

        self.shop_interval_clear()
        PRIVATE_QUARTERS_SHOP_CHECK.clear_offset()

        for _ in self.loop():

            # End
            if after_confirm_state():
                break

            if self.appear(PRIVATE_QUARTERS_SHOP_CHECK, interval=3):
                self.device.click(item)
                continue
            if self.appear_then_click(PRIVATE_QUARTERS_SHOP_AMOUNT_MAX, offset=(20, 20), interval=1):
                continue
            if self.appear_then_click(PRIVATE_QUARTERS_SHOP_CONFIRM_AMOUNT, offset=(20, 20), interval=1):
                continue

        click_timer = Timer(3, count=6)
        for _ in self.loop():
            # End
            if after_purchase_state():
                break

            if click_timer.reached() and after_confirm_state():
                self.device.click(PRIVATE_QUARTERS_SHOP_CHECK)
                click_timer.reset()
                continue

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

                # After purchase, navbars are weirdly
                # reset to default positions
                # So move back for next scan
                self.shop_left_navbar_ensure(2)
                self.shop_bottom_navbar_ensure(2)

                continue

        logger.warning('Too many items to buy, stopped')
        return True
