from module.base.button import ButtonGrid
from module.base.decorator import cached_property, del_cached_property
from module.base.timer import Timer
from module.handler.assets import POPUP_CANCEL, POPUP_CONFIRM
from module.logger import logger
from module.map_detection.utils import Points
from module.shop.assets import *
from module.shop.base import ShopItemGrid
from module.shop.clerk import ShopClerk
from module.shop.shop_port_preset import PORT_SHOP_PRESET
from module.shop.shop_status import ShopStatus
from module.ui.navbar import Navbar
from module.ui.scroll import AdaptiveScroll

#PORT_SHOP_SCROLL = Scroll(PORT_SHOP_SCROLL_AREA, color=(148, 174, 231))
#PORT_SHOP_SCROLL.color_threshold = 210
#PORT_SHOP_SCROLL.edge_threshold = 0.05
#PORT_SHOP_SCROLL.drag_threshold = 0.05
PORT_SHOP_SCROLL = AdaptiveScroll(
    PORT_SHOP_SCROLL_AREA.button,
    parameters={
        'height': 255 - 99
    },
    name="PORT_SHOP_SCROLL")
TEMPLATE_YELLOW_COINS_ICON = Template('./assets/shop/os_cost/YellowCoins.png')
TEMPLATE_PURPLE_COINS_ICON = Template('./assets/shop/os_cost/PurpleCoins.png')


class PortShop(ShopClerk, ShopStatus):
    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        if self.config.OpsiShop_PresetFilter != 'custom':
            return PORT_SHOP_PRESET[self.config.OpsiShop_PresetFilter]
        return self.config.OpsiShop_CustomFilter.strip()

    def _get_coins(self):
        """
        Returns:
            np.array: [[x1, y1], [x2, y2]], location of the coins icon upper-left corner.
        """
        left_column = self.image_crop((356, 206, 1093, 693))
        coins = TEMPLATE_YELLOW_COINS_ICON.match_multi(left_column, similarity=0.75, threshold=5)
        coins.extend(TEMPLATE_PURPLE_COINS_ICON.match_multi(left_column, similarity=0.60, threshold=5))
        coins = Points([(0., c.area[1]) for c in coins]).group(threshold=5)
        logger.attr('Coins_icon', len(coins))
        return coins

    def wait_until_coin_appear(self, skip_first_screenshot=True):
        """
        After entering port shop page,
        items are not loaded that fast,
        wait until any port icon appears
        """
        timeout = Timer(1, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            coins = self._get_coins()

            if timeout.reached():
                break
            if len(coins):
                break

    @cached_property
    def shop_grid(self):
        """
        Returns:
            ButtonGrid:
        """
        # (356, 206, 1093, 688)
        coins = self._get_coins()
        count = len(coins)
        if count == 0:
            logger.warning('Unable to find coin icon, assume item list is at top')
            origin_y = 218
            delta_y = 215
            row = 2
        elif count == 1:
            y_list = coins[:, 1]
            # +206, top of the crop area in _get_coins()
            # -128, from the top of coin icon to the top of shop item
            origin_y = y_list[0] + 206 - 128
            delta_y = 215
            row = 1
        elif count == 2:
            y_list = coins[:, 1]
            y1, y2 = y_list[0], y_list[1]
            origin_y = min(y1, y2) + 206 - 128
            delta_y = abs(y1 - y2)
            row = 2
        else:
            logger.warning(f'Unexpected coin icon match result: {[c.area for c in coins]}')
            origin_y = 218
            delta_y = 215
            row = 2

        # Make up a ButtonGrid
        # Original grid is:
        # shop_grid = ButtonGrid(
        #     origin=(356, 200), delta=(160, 191), button_shape=(98, 98), grid_shape=(5, 2), name='SHOP_GRID')
        if self.config.SERVER in ['cn', 'jp', 'tw']:
            shop_grid = ButtonGrid(
                origin=(356, origin_y), delta=(160, delta_y), button_shape=(98, 98), grid_shape=(5, row),
                name='SHOP_GRID')
        else:
            shop_grid = ButtonGrid(
                origin=(356, origin_y), delta=(160, delta_y), button_shape=(98, 98), grid_shape=(5, row),
                name='SHOP_GRID')
        return shop_grid

    shop_template_folder = './assets/shop/os'

    @cached_property
    def shop_port_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid
        shop_port_items = ShopItemGrid(
            shop_grid,
            templates={}, amount_area=(60, 74, 96, 95),
            price_area=(52, 132, 132, 162))
        shop_port_items.load_template_folder(self.shop_template_folder)
        shop_port_items.load_cost_template_folder('./assets/shop/os_cost')
        shop_port_items.similarity = 0.89
        shop_port_items.cost_similarity = 0.5
        return shop_port_items

    def shop_items(self):
        """
        Shared alias name for all shops,
        so to use  @Config must define
        a unique alias as cover

        Returns:
            ShopItemGrid:
        """
        return self.shop_port_items

    def shop_currency(self):
        """
        Ocr shop coins currency
        Then return yellow coins count

        Returns:
            int: yellow coins amount
        """
        self._currency = self.status_get_yellow_coins()
        self.purple_coins = self.status_get_purple_coins()
        logger.info(f'Yellow coins: {self._currency}, '
                    f'Purple coins: {self.purple_coins}')
        return self._currency

    def shop_check_item(self, item):
        """
        Args:
            item: Item to check

        Returns:
            bool: whether item can be bought
        """
        if item.cost == 'YellowCoins':
            if item.price > self._currency:
                return False
            return True

        if item.cost == 'PurpleCoins':
            if item.price > self.purple_coins:
                return False
            return True

        return False

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
        Handle shop port buy interface if detected

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
        if self.handle_popup_confirm(name='SHOP_BUY_PORT', offset=(20, 50)):
            return True

        return False

    @cached_property
    def _shop_port_navbar(self):
        """
        limited_sidebar 4 options
            NY
            Liverpool
            Gibraltar
            St. Petersburg
        """
        shop_port_navbar = ButtonGrid(
            origin=(44, 266), delta=(0, 87),
            button_shape=(231, 46), grid_shape=(1, 4),
            name='PORT_SHOP_NAVBAR')

        return Navbar(grids=shop_port_navbar,
                      active_color=(43, 94, 248), active_threshold=221,
                      inactive_color=(12, 58, 86), inactive_threshold=221)

    def run(self):
        """
        Run Port Shop

        Returns:
            bool: True,  completed full browse of all shops
                  False, premature stop due to low currency
        """
        # Base case; exit run if filter empty
        if not self.shop_filter:
            return

        # When called, expected to be in
        # correct Port Shop interface
        logger.hr('Port Shop', level=1)
        self.wait_until_coin_appear()

        # Prepare buy operations
        # Sift through all ports to
        # remove "new" label
        ports = self._shop_port_navbar.grids.buttons
        for port in ports:
            # Short sleep, too fast can mis-click
            self.device.click(port)
            self.device.sleep(1)

        # Execute buy operations
        for port in ports:
            self.device.click(port)
            PORT_SHOP_SCROLL.set_top(main=self)
            self.wait_until_coin_appear()
            while 1:
                # Delete cache before item scan
                # Due to multi port options
                del_cached_property(self, 'shop_grid')
                del_cached_property(self, 'shop_port_items')
                if not self.shop_buy():
                    return False

                # Next action based on current scroll position
                if PORT_SHOP_SCROLL.at_bottom(main=self):
                    logger.info('Port Shop reach bottom, stop')
                    break
                else:
                    # Higher scroll rate risks skipping entire rows
                    # Lower scroll rate but clear_click_record
                    # every time to mitigate stuck detection
                    PORT_SHOP_SCROLL.next_page(main=self, page=0.36)
                    self.device.click_record_clear()
                    continue

        return True