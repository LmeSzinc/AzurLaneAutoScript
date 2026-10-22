import re

from jellyfish import levenshtein_distance

import module.config.server as server
from module.base.button import ButtonGrid
from module.base.decorator import cached_property, del_cached_property
from module.island.data import DIC_ISLAND_SHOP, DIC_ISLAND_SHOP_ITEM_TO_RECIPE, DIC_ISLAND_SHOP_RECIPE
from module.island.utils import item_name_with_id
from module.island_handler.assets import *
from module.island_handler.shop_ui import IslandShopUI
from module.logger import logger
from module.ocr.ocr import Digit, Ocr
from module.ui.navbar import Navbar
from module.ui.page import page_island_shop
from module.ui_white.assets import BACK_ARROW_WHITE

SHOP_ITEM_NAME_AREA = (12, 142, 134, 163)


def shop_recipe_name_with_id(recipe_id):
    if recipe_id not in DIC_ISLAND_SHOP_RECIPE:
        return f'unknown shop recipe ({recipe_id})'
    return f"{DIC_ISLAND_SHOP_RECIPE[recipe_id]['name'][server.server]} ({recipe_id})"


class ProductNameOcr(Ocr):
    """OCR of island product names.

    cnocr takes a glyph stroke or an edge of the item icon as punctuation, such
    as `小\\麦种子` for `小麦种子` or `_大米` for `大米`. Those characters never
    belong to a product name, so they are removed here, and the misreads that
    are not punctuation are revised to the real name, so that
    item_name_to_recipe_id does not have to guess by edit distance.
    """

    def after_process(self, result):
        """
        Args:
            result (str): '小\\麦种子'

        Returns:
            str: '小麦种子'
        """
        result = super().after_process(result)
        prev = result

        # Punctuation, symbols and stroke fragments read from the glyph strokes
        # and the item icon, e.g. `小\麦种子`, `_大米` and `大米”`. Covers ASCII
        # punctuation (!-/ :-@ [-` {-~), general punctuation (\u2000-\u206f,
        # quotes and dashes), CJK punctuation (\u3000-\u303f), fullwidth forms
        # (\uff00-\uffef) and 丶, the stroke of the first glyph of `小麦`
        result = re.sub(r'[\u2000-\u206f\u3000-\u303f\uff00-\uffef!-/:-@\[-`{-~丶]', '', result)
        if server.server == 'en':
            # Latin product names keep the space between words
            result = re.sub(r'\s+', ' ', result).strip()
        else:
            # Latin letters and digits never appear in a CJK product name
            result = re.sub(r'[A-Za-z0-9]', '', result)
            result = re.sub(r'\s+', '', result)
        # 眸牛饲料 -> 哞哞牛饲料, the doubled prefix is read as a single glyph
        result = re.sub(r'^[眸哞]牛饲料$', '哞哞牛饲料', result)

        if result != prev:
            logger.info(f'OCR {self.name}: Result "{prev}" is revised to "{result}"')
        return result


class IslandShop(IslandShopUI):
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
        elif server.server == 'tw':
            lang = 'tw'
        else:
            lang = 'cnocr'
        return ProductNameOcr(
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
        for _ in self.loop(timeout=5):
            names = self._island_shop_item_name_ocr.ocr(self.device.image)
            ids = [self.item_name_to_recipe_id(name) for name in names]  # need to keep all ids to pair with buttons
            if all(id is None for id in ids):
                logger.warning(f"Failed to get item ids from names {names}, retrying...")
                continue
            return ids
        else:
            logger.warning("Failed to get item ids, return empty list")
            return [None] * len(self._island_shop_item_name_grid.buttons)

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

        if server.server in ['cn', 'tw']:
            lang = 'cnocr'
        else:
            lang = 'azur_lane'
        ocr = Digit([ISLAND_SHOP_BUY_AMOUNT], lang=lang, letter=(57, 58, 60), threshold=160, name="island_shop_buy_amount_ocr")
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
        required = DIC_ISLAND_SHOP_RECIPE[recipe_id]['resource_consume'][currency_id] * amount
        # Items paid as currency, e.g. wheat for flour, keep their protected stock
        protected = self.get_protected_items([currency_id]).get(currency_id, 0) if currency_id != 1 else 0
        logger.info(
            f'Current {item_name_with_id(currency_id)} amount: {currency_amount}, '
            f'protected: {protected}, required: {required}'
        )
        if currency_amount - protected < required:
            logger.warning(
                f'Not enough {item_name_with_id(currency_id)} to buy {amount} of '
                f'{shop_recipe_name_with_id(recipe_id)}'
            )
            return False
        for id, button in zip(self.island_shop_item_ids, self._island_shop_item_grid.buttons):
            if id == recipe_id:
                self.island_shop_buy_execute(button, amount)
                return True
        logger.warning(f'{shop_recipe_name_with_id(recipe_id)} not found in shop')
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
            active_threshold=30,
            inactive_threshold=15,
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
                logger.info(
                    f'{shop_recipe_name_with_id(recipe_id)} is in shop '
                    f'{DIC_ISLAND_SHOP[shop_id]["name"][server.server]} ({shop_id})'
                )
                break
        if target_shop_id is None:
            logger.warning(f'{shop_recipe_name_with_id(recipe_id)} is not available in the searched shops')
            return False
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
            logger.info(
                f'Buying {amount} of {item_name_with_id(item_id)} requires '
                f'{shop_recipe_name_with_id(recipe_id)} with buy count {buy_count}'
            )
            if self.island_shop_set_navbar_and_tab(recipe_id, isolated=isolated):
                if not self.island_shop_buy_in_page(recipe_id, buy_count):
                    logger.warning(f'Failed to buy {shop_recipe_name_with_id(recipe_id)}')
                    success = False
            else:
                logger.warning(
                    f'Failed to set tabs for {shop_recipe_name_with_id(recipe_id)}, cannot buy'
                )
                success = False
        return success
