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

        # Helper negate function to ensure purchase has finished
        def after_purchase():
            return (not self.appear(PRIVATE_QUARTERS_SHOP_WEEKLY_ROSES_GET, offset=(20, 20)) and
                    not self.appear(PRIVATE_QUARTERS_SHOP_WEEKLY_CAKES_GET, offset=(20, 20)))

        self.shop_interval_clear()
        PRIVATE_QUARTERS_SHOP_CHECK.clear_offset()

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if (self.appear(PRIVATE_QUARTERS_SHOP_WEEKLY_ROSES_GET, offset=(20, 20)) or
                    self.appear(PRIVATE_QUARTERS_SHOP_WEEKLY_CAKES_GET, offset=(20, 20))):
                self.ui_click(
                    click_button=PRIVATE_QUARTERS_SHOP_CHECK,
                    check_button=after_purchase,
                    offset=(20, 20),
                    skip_first_screenshot=True
                )
                break

            if self.appear(PRIVATE_QUARTERS_SHOP_CHECK, interval=1):
                self.device.click(item)
                continue
            if self.appear_then_click(PRIVATE_QUARTERS_SHOP_AMOUNT_MAX, offset=(20, 20), interval=1):
                continue
            if self.appear_then_click(PRIVATE_QUARTERS_SHOP_CONFIRM_AMOUNT, offset=(20, 20), interval=1):
                continue
