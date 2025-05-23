from module.base.button import ButtonGrid
from module.base.decorator import cached_property, del_cached_property
from module.base.timer import Timer
from module.config.redirect_utils.shop_filter import voucher_redirect
from module.handler.assets import POPUP_CANCEL, POPUP_CONFIRM
from module.logger import logger
from module.map_detection.utils import Points
from module.shop.assets import *
from module.shop.base import ShopItemGrid
from module.shop.clerk import ShopClerk
from module.shop.shop_status import ShopStatus
from module.ui.scroll import Scroll

VOUCHER_SHOP_SCROLL = Scroll(VOUCHER_SHOP_SCROLL_AREA, color=(255, 255, 255))
TEMPLATE_VOUCHER_ICON = Template('./assets/shop/cost/Voucher.png')


class VoucherShop(ShopClerk, ShopStatus):
    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        return voucher_redirect(self.config.OpsiVoucher_Filter.strip())

    def _get_vouchers(self):
        """
        Returns:
            np.array: [[x1, y1], [x2, y2]], location of the voucher icon upper-left corner.
        """
        left_column = self.image_crop((305, 306, 1256, 646), copy=False)
        vouchers = TEMPLATE_VOUCHER_ICON.match_multi(left_column, similarity=0.75, threshold=5)
        vouchers = Points([(0., v.area[1]) for v in vouchers]).group(threshold=5)
        logger.attr('Vouchers_icon', len(vouchers))
        return vouchers

    def wait_until_voucher_appear(self, skip_first_screenshot=True):
        """
        After entering voucher shop page,
        items are not loaded that fast,
        wait until any voucher icon appears
        """
        timeout = Timer(1, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            vouchers = self._get_vouchers()

            if timeout.reached():
                break
            if len(vouchers):
                break

    @cached_property
    def shop_grid(self):
        """
        Returns:
            ButtonGrid:
        """
        vouchers = self._get_vouchers()
        count = len(vouchers)
        if count == 0:
            logger.warning('Unable to find voucher icon, assume item list is at top')
            origin_y = 200
            delta_y = 191
            row = 2
        elif count == 1:
            y_list = vouchers[:, 1]
            # +306, top of the crop area in _get_vouchers()
            # -133, from the top of voucher icon to the top of shop item
            origin_y = y_list[0] + 306 - 133
            delta_y = 191
            row = 1
        elif count == 2:
            y_list = vouchers[:, 1]
            y1, y2 = y_list[0], y_list[1]
            origin_y = min(y1, y2) + 306 - 133
            delta_y = abs(y1 - y2)
            row = 2
        else:
            logger.warning(f'Unexpected voucher icon match result: {[v.area for v in vouchers]}')
            origin_y = 200
            delta_y = 191
            row = 2

        # Make up a ButtonGrid
        # Original grid is:
        # shop_grid = ButtonGrid(
        #     origin=(463, 200), delta=(156, 191), button_shape=(99, 99), grid_shape=(5, 2), name='SHOP_GRID')
        if self.config.SERVER in ['cn', 'jp', 'tw']:
            shop_grid = ButtonGrid(
                origin=(305, origin_y), delta=(189.5, delta_y), button_shape=(99, 99), grid_shape=(5, row),
                name='SHOP_GRID')
        else:
            shop_grid = ButtonGrid(
                origin=(463, origin_y), delta=(156, delta_y), button_shape=(99, 99), grid_shape=(5, row),
                name='SHOP_GRID')
        return shop_grid

    shop_template_folder = './assets/shop/voucher'

    @cached_property
    def shop_voucher_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_voucher_items = ShopItemGrid(
            shop_grid,
            templates={}, amount_area=(60, 74, 96, 95),
            price_area=(52, 132, 132, 162))
        shop_voucher_items.load_template_folder(self.shop_template_folder)
        shop_voucher_items.load_cost_template_folder('./assets/shop/cost')
        shop_voucher_items.similarity = 0.85
        shop_voucher_items.cost_similarity = 0.5
        return shop_voucher_items

    def shop_items(self):
        """
        Shared alias name for all shops,
        so to use  @Config must define
        a unique alias as cover

        Returns:
            ShopItemGrid:
        """
        return self.shop_voucher_items

    def shop_currency(self):
        """
        Ocr shop voucher currency
        Then return voucher count

        Returns:
            int: voucher amount
        """
        self._currency = self.status_get_voucher()
        logger.info(f'Voucher: {self._currency}')
        return self._currency

    def shop_interval_clear(self):
        """
        Clear interval on select assets for
        shop_buy_handle
        """
        super().shop_interval_clear()
        self.interval_clear([
            SHOP_BUY_CONFIRM_SELECT,
            SHOP_BUY_CONFIRM_AMOUNT,
            POPUP_CONFIRM,
            POPUP_CANCEL,
        ])

    def shop_buy_handle(self, item):
        """
        Handle shop_voucher buy interface if detected

        Args:
            item: Item to handle

        Returns:
            bool: whether interface was detected and handled
        """
        if self.appear(SHOP_BUY_CONFIRM_SELECT, offset=(20, 20), interval=3):
            self.shop_buy_select_execute(item)
            self.interval_reset(SHOP_BUY_CONFIRM_SELECT)
            return True
        if self.appear(SHOP_BUY_CONFIRM_AMOUNT, offset=(20, 20), interval=3):
            self.shop_buy_amount_execute(item)
            self.interval_reset(SHOP_BUY_CONFIRM_AMOUNT)
            return True
        if self.handle_popup_confirm(name='SHOP_BUY_VOUCHER', offset=(20, 50)):
            return True
        if self.config.SERVER in ['cn', 'jp', 'tw']:
            # A button named `Exchange` when buying item in amount of 1.
            if self.appear_then_click(SHOP_BUY_CONFIRM_AMOUNT, offset=(-20, -160, 20, -120), interval=3):
                return True

        return False

    def run(self):
        """
        Run Voucher Shop
        """
        # Base case; exit run if filter empty
        if not self.shop_filter:
            return

        # When called, expected to be in
        # correct Voucher Shop interface
        logger.hr('Voucher Shop', level=1)
        self.wait_until_voucher_appear()

        # Execute buy operations
        VOUCHER_SHOP_SCROLL.set_top(main=self)
        while 1:
            self.shop_buy()
            if VOUCHER_SHOP_SCROLL.at_bottom(main=self):
                logger.info('Voucher Shop reach bottom, stop')
                break
            else:
                VOUCHER_SHOP_SCROLL.next_page(main=self)
                del_cached_property(self, 'shop_grid')
                del_cached_property(self, 'shop_voucher_items')
                continue

    def run_once(self):
        """
        Run Voucher Shop to purchase
        a single logger archive type
        item

        Returns:
            bool
        """
        # Replace filter
        self.shop_filter = 'LoggerArchive'

        # When called, expected to be in
        # correct Voucher Shop interface
        logger.hr('Voucher Shop Once', level=1)
        self.wait_until_voucher_appear()

        # Execute buy operations
        items = self.shop_get_items()
        self.shop_currency()
        if self._currency <= 0:
            logger.warning(f'Current funds: {self._currency}, stopped')
            return False

        item = self.shop_get_item_to_buy(items)
        if item is None:
            logger.info('No logger archives available for purchase')
            return False
        self.shop_buy_execute(item)

        logger.info('Purchased single logger archive')
        return True
