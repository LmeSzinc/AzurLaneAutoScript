from jellyfish import levenshtein_distance

import module.config.server as server
from module.base.decorator import cached_property, del_cached_property
from module.base.button import ButtonGrid
from module.island.data import DIC_ISLAND_SHOP, DIC_ISLAND_SHOP_ITEM_TO_RECIPE, DIC_ISLAND_SHOP_RECIPE
from module.island.ui import IslandUI, NestedNavbar
from module.island_handler.assets import *
from module.logger import logger
from module.ocr.ocr import Digit, Ocr
from module.ui.assets import ISLAND_GOTO_ISLAND_SHOP
from module.ui.navbar import Navbar
from module.ui.page import page_island, page_island_shop
from module.ui_white.assets import BACK_ARROW_WHITE


SHOP_ITEM_NAME_AREA = (12, 142, 134, 163)


class IslandShop(IslandUI):
    has_shop_banner = False

    def ui_goto_island_shop(self):
        self.ui_goto(page_island)
        for _ in self.loop():
            if self.ui_page_appear(page_island_shop, offset=(0, 20)):
                return True
            elif self.appear(ISLAND_SHOP_MILL_CHECK, offset=(20, 20)):
                return True
            elif self.appear(ISLAND_SHOP_RECOMMEND, offset=(0, 20)):
                self.has_shop_banner = True
                return True
            if self.appear_then_click(ISLAND_GOTO_ISLAND_SHOP, offset=(20, 20), interval=1):
                continue

    @cached_property
    def _island_shop_side_navbar(self):
        if not self.has_shop_banner:
            return NestedNavbar(
                grids=ButtonGrid(origin=(12, 80), delta=(0, 70), button_shape=(127, 70), grid_shape=(1, 6), name='ISLAND_SHOP_NAVBAR'),
                subgrid_delta=(0, 58), subgrid_button_shape=(127, 58),
                subgrid_shapes=[(1, 1), (1, 2), (1, 1), (1, 1), (1, 2), (1, 0)],
                direction='vertical',
            )
        else:
            return NestedNavbar(
                grids=ButtonGrid(origin=(12, 80), delta=(0, 70), button_shape=(127, 70), grid_shape=(1, 7), name='ISLAND_SHOP_NAVBAR'),
                subgrid_delta=(0, 58), subgrid_button_shape=(127, 58),
                subgrid_shapes=[(1, 0), (1, 1), (1, 2), (1, 1), (1, 1), (1, 2), (1, 0)],
                direction='vertical',
            )

    def island_shop_side_navbar_ensure(self, main_index, sub_index=None, skip_first_screenshot=True):
        if not self.has_shop_banner:
            return self._island_shop_side_navbar.set(self, main_index=main_index, sub_index=sub_index, skip_first_screenshot=skip_first_screenshot)
        else:
            return self._island_shop_side_navbar.set(self, main_index=main_index+1, sub_index=sub_index, skip_first_screenshot=skip_first_screenshot)

    @property
    def _island_shop_item_grid(self):
        return ButtonGrid(
            origin=(224, 184),
            delta=(163, 226),
            button_shape=(147, 201),
            grid_shape=(6, 2),
            name="island_shop_item_grid",
        )

    @property
    def _island_shop_item_name_grid(self):
        return self._island_shop_item_grid.crop(
            SHOP_ITEM_NAME_AREA,
            name="island_shop_item_name_grid",
        )

    @property
    def _island_shop_item_name_ocr(self):
        if server.server == 'jp':
            lang = 'jp'
        elif server.server == 'cn':
            lang = 'cnocr'
        else:
            lang = 'azur_lane'
        return Ocr(
            self._island_shop_item_name_grid.buttons,
            lang=lang,
            letter=(66, 66, 66),
            threshold=200,
            name="island_shop_item_name_ocr",
        )

    def item_name_to_recipe_id(self, name):
        if name == '':
            return None
        min_distance = float('inf')
        min_real_distance = float('inf')
        corrected_name = None
        corrected_id = None
        for recipe_id, recipe in DIC_ISLAND_SHOP_RECIPE.items():
            recipe_name = recipe['name'][server.server]
            if isinstance(name, str) and isinstance(recipe_name, str) and len(recipe_name) >= len(name) and len(name) > 0:
                best_sub_distance = float('inf')
                L = len(name)
                for i in range(len(recipe_name) - L + 1):
                    sub = recipe_name[i:i+L]
                    d = levenshtein_distance(name, sub)
                    if d < best_sub_distance:
                        best_sub_distance = d
                distance = best_sub_distance
                real_distance = levenshtein_distance(name, recipe_name)
            else:
                distance = levenshtein_distance(name, recipe_name)
                real_distance = distance
            if distance < min_distance or (distance == min_distance and real_distance < min_real_distance):
                min_distance = distance
                min_real_distance = real_distance
                corrected_name = recipe_name
                corrected_id = recipe_id
        if min_real_distance > 0:
            logger.info(f"Corrected '{name}' to '{corrected_name}' with distance {min_distance}")
        return corrected_id

    @cached_property
    def island_shop_item_ids(self):
        return self.island_shop_get_item_ids()

    def island_shop_get_item_ids(self):
        names = self._island_shop_item_name_ocr.ocr(self.device.image)
        ids = [self.item_name_to_recipe_id(name) for name in names if name != '']
        return ids

    @property
    def _island_currency_grid(self):
        return ButtonGrid(
            origin=(688, 18),
            delta=(171, 0),
            button_shape=(126, 29),
            grid_shape=(3, 1),
            name="island_currency_grid",
        )

    def island_shop_get_currency(self):
        for _ in self.loop(timeout=5):
            if self.ui_page_appear(page_island_shop):
                # coin is currency
                price_button = self._island_currency_grid.buttons[-1]
                price_ocr = Digit([price_button], letter=(255, 245, 118), threshold=160, name="island_currency_ocr")
                price = price_ocr.ocr(self.device.image)
                if price != 0:
                    return {1: price}
            else:
                # wheat, corn and grass are currency
                price_ocr = Digit(self._island_currency_grid.buttons, letter=(255, 245, 118), threshold=160, name="island_currency_ocr")
                price = price_ocr.ocr(self.device.image)
                if any(p != 0 for p in price):
                    return {2000: price[0], 2001: price[1], 2008: price[2]}
        else:
            logger.warning("Failed to get currency amount, return empty dict")
            return {}

    def island_shop_buy_ensure_amount(self, amount):
        # having button of -10, -1, +1, +10, and the amount to buy, we can ensure the amount to buy by clicking these buttons
        # try using least number of clicks
        def middle_integer(N):
            d = N - 1
            q = d // 10
            r = d % 10
            if r <= 5:
                middle = 10*q + 1
            else:
                middle = 10*(q + 1) + 1
            return middle

        ocr = Digit([ISLAND_SHOP_BUY_AMOUNT], letter=(57, 58, 60), threshold=160, name="island_shop_buy_amount_ocr")
        def one_tenth_ocr(image):
            amount = ocr.ocr(image)
            return amount // 10

        self.ui_ensure_index(middle_integer(amount) // 10, one_tenth_ocr, ISLAND_SHOP_BUY_AMOUNT_PLUS_TEN, ISLAND_SHOP_BUY_AMOUNT_MINUS_TEN)
        self.ui_ensure_index(amount, ocr, ISLAND_SHOP_BUY_AMOUNT_PLUS_ONE, ISLAND_SHOP_BUY_AMOUNT_MINUS_ONE)

    def island_shop_buy_execute(self, button, amount):
        for _ in self.loop():
            if self.appear(ISLAND_SHOP_BUY_CHECK, offset=(20, 20)):
                break
            if self.appear(BACK_ARROW_WHITE, offset=(20, 20), interval=2):
                self.device.click(button)
        self.island_shop_buy_ensure_amount(amount)
        for _ in self.loop():
            if self.handle_island_additional():
                self.interval_reset(BACK_ARROW_WHITE)
                continue
            if self.appear_then_click(ISLAND_SHOP_BUY_CONFIRM, offset=(20, 20), interval=3):
                self.interval_reset(BACK_ARROW_WHITE)
                continue
            if self.appear(BACK_ARROW_WHITE, offset=(20, 20), interval=2):
                break

    def island_shop_buy_in_page(self, recipe_id, amount=1):
        currency_id = list(DIC_ISLAND_SHOP_RECIPE[recipe_id]['resource_consume'].keys())[0]
        currency_amount = self.island_shop_get_currency().get(currency_id, 0)
        logger.info(f"Current currency amount: {currency_amount}, required: {DIC_ISLAND_SHOP_RECIPE[recipe_id]['resource_consume'][currency_id] * amount}")
        if currency_amount < DIC_ISLAND_SHOP_RECIPE[recipe_id]['resource_consume'][currency_id] * amount:
            logger.warning(f"Not enough currency to buy {amount} of recipe {recipe_id}")
            return False
        for id, button in zip(self.island_shop_item_ids, self._island_shop_item_grid.buttons):
            if id == recipe_id:
                self.island_shop_buy_execute(button, amount)
                return True
        logger.warning(f"Recipe {recipe_id} not found in shop")
        return False

    @cached_property
    def _island_shop_tab(self):
        return Navbar(
            grids=ButtonGrid(
                origin=(184, 82),
                delta=(176, 0),
                button_shape=(176, 42),
                grid_shape=(3, 1),
                name="island_shop_tab_grid",
            ),
            active_color=(249, 181, 76),
            inactive_color=(235, 235, 235),
            active_threshold=221,
            inactive_threshold=240,
            active_count=5000,
            inactive_count=5000,
            name="island_shop_tab",
        )

    def island_shop_set_navbar_and_tab(self, recipe_id, isolated=True):
        # only works for general items (skins and items are not included)
        del_cached_property(self, 'island_shop_item_ids')
        success = True
        if isolated:
            search_range = range(10019, 10038)
        else:
            search_range = [*range(10019, 10022), *range(10031, 10038), *range(10109, 10114)]
        target_shop_id = None
        for shop_id in search_range:
            if recipe_id in DIC_ISLAND_SHOP[shop_id]['goods']:
                target_shop_id = shop_id
                logger.info(f"Recipe {recipe_id} is in shop {shop_id}, name {DIC_ISLAND_SHOP[shop_id]['name'][server.server]}")
                break
        order = [0, 0, 0]
        for index in range(3):
            order[2 - index] = DIC_ISLAND_SHOP[target_shop_id]['order']
            target_shop_id = DIC_ISLAND_SHOP[target_shop_id]['parent_id']
            if target_shop_id == 0:
                break
        if not isolated or recipe_id == 103004:
            success = self.island_shop_side_navbar_ensure(main_index=order[0]-1, sub_index=order[1]-1)
        if success and 111101 <= recipe_id < 111300:
            # fishery bug makes freshwater fish, saltwater fish and other products not distinguishable
            # after jumping from details page, so we need to set top tab to specific tab according to the recipe_id
            for index, shop_id in enumerate([10033, 10034, 10035]):
                if recipe_id in DIC_ISLAND_SHOP[shop_id]['goods']:
                    success = self._island_shop_tab.set(main=self, left=index+1)
                    return True
        elif not isolated and success and recipe_id >= 411000:
            for index, shop_id in enumerate([10111, 10112, 10113]):
                if recipe_id in DIC_ISLAND_SHOP[shop_id]['goods']:
                    success = self._island_shop_tab.set(main=self, left=index+1)
                    return True
        return success

    def wait_island_shop_loading(self):
        for _ in self.loop(timeout=5):
            if self.ui_page_appear(page_island_shop, offset=(0, 20)):
                return True
            if self.appear(ISLAND_SHOP_MILL_CHECK, offset=(20, 20)):
                return True
            if self.appear(ISLAND_SHOP_RECOMMEND, offset=(0, 20)):
                self.has_shop_banner = True
                return True
            if self.appear(ISLAND_SHOP_LOADING, offset=(20, 20)):
                continue

    def island_shop_buy(self, shopping_dict={}, isolated=True):
        """
        Parameters:
            shopping_dict (dict): {item_id: amount} of items to buy. item_id is the id of the item in DIC_ISLAND_SHOP_RECIPE. amount is the amount to buy.
            isolated (bool): whether to only buy from isolated shop. If False, will buy from general shop.
                            notice that the behaviour of multiple items to buy and isolated=True is undefined.
        """
        self.wait_island_shop_loading()
        success = True
        for item_id, amount in shopping_dict.items():
            if item_id not in DIC_ISLAND_SHOP_ITEM_TO_RECIPE:
                logger.warning(f"Item {item_id} not found in data, cannot buy")
                continue
            recipe_id = DIC_ISLAND_SHOP_ITEM_TO_RECIPE[item_id]
            if recipe_id not in DIC_ISLAND_SHOP_RECIPE:
                logger.warning(f"Recipe {recipe_id} not found in data, cannot buy")
                continue
            buy_count = (amount - 1) // DIC_ISLAND_SHOP_RECIPE[recipe_id]['items'][item_id] + 1
            logger.info(f"Buying {amount} of item {item_id} requires recipe {recipe_id} with buy count {buy_count}")
            if self.island_shop_set_navbar_and_tab(recipe_id, isolated=isolated):
                if not self.island_shop_buy_in_page(recipe_id, buy_count):
                    logger.warning(f"Failed to buy recipe {recipe_id}")
                    success = False
            else:
                logger.warning(f"Failed to set tabs for recipe {recipe_id}, cannot buy")
                success = False
        return success