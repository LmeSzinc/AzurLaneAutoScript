from collections import namedtuple

import cv2
import numpy as np
from jellyfish import levenshtein_distance

import module.config.server as server
from module.base.button import Button, ButtonGrid
from module.base.timer import Timer
from module.base.utils import color_similarity_2d, crop, extract_letters
from module.exception import GameTooManyClickError
from module.island.data import DIC_ISLAND_EXCHANGE_RECIPE, DIC_ISLAND_ITEM
from module.island.utils import item_name_with_id
from module.island_handler.assets import *
from module.island_handler.shop_ui import IslandShopUI
from module.logger import logger
from module.ocr.ocr import Digit, Ocr

# {fish meat id: {fish id: fish meat per fish}}, every exchange consumes one fish
FISH_MEAT_SOURCES = {
    meat_id: {
        fish_id: recipe['items'][meat_id]
        for recipe in DIC_ISLAND_EXCHANGE_RECIPE.values() if meat_id in recipe['items']
        for fish_id in recipe['resource_consume']
    }
    for meat_id in (2521, 2522)
}
FISH_MEAT_YIELD = {fish_id: amount for sources in FISH_MEAT_SOURCES.values() for fish_id, amount in sources.items()}
# Sub tab of the fish meat processing page in the island shop side navbar
FISH_MEAT_TAB = {2521: 0, 2522: 1}

# Fish cards, 4 per row. Only fish in stock are shown, sorted by item id.
EXCHANGE_FISH_GRID = ButtonGrid(
    origin=(215, 111), delta=(131.33, 155), button_shape=(104, 108), grid_shape=(4, 2), name='EXCHANGE_FISH_GRID')
EXCHANGE_FISH_NAME_GRID = EXCHANGE_FISH_GRID.crop((-2, 111, 106, 138), name='EXCHANGE_FISH_NAME_GRID')
EXCHANGE_FISH_STOCK_GRID = EXCHANGE_FISH_GRID.crop((56, 86, 106, 110), name='EXCHANGE_FISH_STOCK_GRID')
# Selected amount above the card top left, shown once selected
EXCHANGE_FISH_COUNT_GRID = EXCHANGE_FISH_GRID.crop((34, -7, 81, 20), name='EXCHANGE_FISH_COUNT_GRID')
# Minus button above the card top right. Clicked on its part outside the card,
# since a click on the card selects one more fish.
EXCHANGE_FISH_MINUS_GRID = EXCHANGE_FISH_GRID.crop((105, -5, 116, 17), name='EXCHANGE_FISH_MINUS_GRID')
EXCHANGE_FISH_NAME_BACKGROUND = (112, 112, 115)
ISLAND_EXCHANGE_CLEAR = Button(
    area=(375, 630, 423, 677), color=(), button=(375, 630, 423, 677), name='ISLAND_EXCHANGE_CLEAR')


class FishStockDigit(Digit):
    """Fish stock on the dark badge at the card bottom right."""

    def pre_process(self, image):
        # Keep the badge only, the light card face around it would read as digits
        ys, xs = np.where(image.max(axis=2) < 130)
        if len(xs):
            image = image[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        image = extract_letters(image, letter=self.letter, threshold=self.threshold)
        return cv2.copyMakeBorder(image, 3, 3, 3, 3, cv2.BORDER_CONSTANT, value=255)


EXCHANGE_FISH_STOCK_OCR = FishStockDigit([], lang='cnocr', letter=(255, 255, 255), threshold=128,
                                         name='EXCHANGE_FISH_STOCK')
EXCHANGE_FISH_COUNT_OCR = Digit([], lang='cnocr', letter=(255, 235, 85), threshold=128, name='EXCHANGE_FISH_COUNT')
# Fish meat owned in dark digits, and the gain of the selected fish in blue digits after it
EXCHANGE_MEAT_OWNED_OCR = Digit(ISLAND_EXCHANGE_TOTAL_AMOUNT, lang='cnocr', letter=(60, 60, 60), threshold=160,
                                name='EXCHANGE_MEAT_OWNED')
EXCHANGE_MEAT_GAIN_OCR = Digit(ISLAND_EXCHANGE_TOTAL_AMOUNT, lang='cnocr', letter=(57, 191, 255), threshold=128,
                               name='EXCHANGE_MEAT_GAIN')

# before, after (int): Fish meat owned before and after the exchange.
# stock (dict): {fish id: stock} before the exchange.
FishMeatExchange = namedtuple('FishMeatExchange', ['before', 'after', 'stock'])


def fish_name_to_id(name, meat_id):
    """
    Args:
        name (str): Fish name OCR result.
        meat_id (int): Fish meat of the page, which limits the candidates.

    Returns:
        int: Fish id of the closest name on the current server, None if empty or ambiguous.
    """
    if not name:
        return None
    distances = sorted(
        (levenshtein_distance(name, DIC_ISLAND_ITEM[fish_id]['name'][server.server]), fish_id)
        for fish_id in FISH_MEAT_SOURCES[meat_id]
    )
    if len(distances) > 1 and distances[0][0] == distances[1][0]:
        return None
    return distances[0][1]


def read_fish_cards(image, meat_id):
    """
    Args:
        image (np.ndarray): Screenshot of the fish meat processing page.
        meat_id (int):

    Returns:
        list[tuple[int, int, int]]: (card index, fish id, stock) of shown cards,
            fish id is None if the name is not recognized.
    """
    indices = [
        index for index, button in enumerate(EXCHANGE_FISH_NAME_GRID.buttons)
        if np.mean(color_similarity_2d(crop(image, button.area), EXCHANGE_FISH_NAME_BACKGROUND) > 235) > 0.5
    ]
    if not indices:
        return []
    if server.server == 'jp':
        lang = 'jp'
    elif server.server == 'tw':
        lang = 'tw'
    else:
        lang = 'cnocr'
    name_ocr = Ocr([], lang=lang, letter=(255, 255, 255), threshold=128, name='EXCHANGE_FISH_NAME')
    names = name_ocr.ocr([crop(image, EXCHANGE_FISH_NAME_GRID.buttons[i].area) for i in indices], direct_ocr=True)
    stocks = EXCHANGE_FISH_STOCK_OCR.ocr(
        [crop(image, EXCHANGE_FISH_STOCK_GRID.buttons[i].area) for i in indices], direct_ocr=True)
    return [(index, fish_name_to_id(name, meat_id), stock) for index, name, stock in zip(indices, names, stocks)]


def read_fish_counts(image, indices):
    """
    Returns:
        list[int]: Selected amount of each card in indices, 0 if not selected.
    """
    if not indices:
        return []
    return EXCHANGE_FISH_COUNT_OCR.ocr(
        [crop(image, EXCHANGE_FISH_COUNT_GRID.buttons[i].area) for i in indices], direct_ocr=True)


def read_fish_meat(image):
    """
    Returns:
        tuple[int, int]: Fish meat owned, fish meat gained from the selected fish.
    """
    return EXCHANGE_MEAT_OWNED_OCR.ocr(image), EXCHANGE_MEAT_GAIN_OCR.ocr(image)


def get_fish_exchange_amounts(stock, keep=None):
    """
    Args:
        stock (dict): {fish id: stock}
        keep (dict): {fish id: amount to keep}, None to keep nothing.

    Returns:
        dict: {fish id: amount to exchange}
    """
    keep = keep or {}
    return {fish_id: max(amount - max(keep.get(fish_id, 0), 0), 0) for fish_id, amount in stock.items()}


def get_fish_meat_gain(amounts):
    return sum(FISH_MEAT_YIELD[fish_id] * amount for fish_id, amount in amounts.items())


class IslandExchange(IslandShopUI):
    def get_fish_keep_items(self):
        """
        Returns:
            dict: {fish id: amount} protected from exchange, the hard floor,
                restaurant reserve and task target of each fish.
        """
        return self.get_protected_items(FISH_MEAT_YIELD)

    def _exchange_clear_selection(self):
        """
        Returns:
            int: Fish meat owned, None if selection is not cleared.
        """
        click_timer = Timer(1, count=2)
        for _ in self.loop(timeout=5):
            if self.handle_island_additional():
                continue
            owned, gain = read_fish_meat(self.device.image)
            if gain == 0:
                return owned
            if click_timer.reached_and_reset():
                self.device.click(ISLAND_EXCHANGE_CLEAR)
        logger.warning('Unable to clear fish selection')
        return None

    def _exchange_read_cards(self, meat_id):
        """
        Returns:
            list[tuple[int, int, int]]: (card index, fish id, stock), same as in two
                screenshots in a row, None if not readable.
        """
        last = None
        for _ in self.loop(timeout=5):
            if self.handle_island_additional():
                continue
            cards = read_fish_cards(self.device.image, meat_id)
            if any(fish_id is None or stock <= 0 for _, fish_id, stock in cards):
                logger.info(f'Unrecognized fish card: {cards}')
                last = None
                continue
            if cards == last:
                return cards
            last = cards
        logger.warning('Unable to read fish cards')
        return None

    def _exchange_select_all(self):
        for _ in self.loop(timeout=3):
            if self.handle_island_additional():
                continue
            if self.image_color_count(ISLAND_EXCHANGE_SELECT_ALL, color=(255, 255, 255), count=25):
                return True
            if self.appear_then_click(ISLAND_EXCHANGE_SELECT_ALL, offset=(20, 20), interval=1):
                continue
        logger.warning('Unable to select all fish')
        return False

    def _exchange_set_count(self, index, amount):
        ocr = Digit([EXCHANGE_FISH_COUNT_GRID.buttons[index]], lang='cnocr', letter=EXCHANGE_FISH_COUNT_OCR.letter,
                    threshold=EXCHANGE_FISH_COUNT_OCR.threshold, name='EXCHANGE_FISH_COUNT')
        try:
            self.ui_ensure_index(amount, letter=ocr, next_button=EXCHANGE_FISH_GRID.buttons[index],
                                 prev_button=EXCHANGE_FISH_MINUS_GRID.buttons[index], skip_first_screenshot=True)
            return True
        except GameTooManyClickError:
            logger.warning(f'Too many clicks when setting fish card {index} to {amount}')
            return False

    def island_exchange_fish_meat(self, meat_id, keep=None):
        """
        Exchange fish above keep into fish meat, in the island shop.

        Args:
            meat_id (int): 2521 Freshwater Fish Meat or 2522 Saltwater Fish Meat.
            keep (dict): {fish id: amount} not to exchange, None to exchange all fish.

        Returns:
            FishMeatExchange: None if the exchange failed.
        """
        logger.info(f'Exchange fish into {item_name_with_id(meat_id)}, keep: {keep or {}}')
        self.island_shop_side_navbar_ensure(main_index=6, sub_index=FISH_MEAT_TAB[meat_id])
        before = self._exchange_clear_selection()
        if before is None:
            return None
        cards = self._exchange_read_cards(meat_id)
        if cards is None:
            return None
        stock = {fish_id: amount for _, fish_id, amount in cards}
        amounts = get_fish_exchange_amounts(stock, keep)
        expected = get_fish_meat_gain(amounts)
        logger.info(f'Fish stock: {stock}, exchange: {amounts}, expected fish meat gain: {expected}')
        if expected <= 0:
            return FishMeatExchange(before, before, stock)

        # Start from all fish selected if fewer fish are to be kept than exchanged
        if sum(stock.values()) - sum(amounts.values()) < sum(amounts.values()):
            if not self._exchange_select_all():
                self._exchange_clear_selection()
                return None
        for index, fish_id, _ in cards:
            if not self._exchange_set_count(index, amounts[fish_id]):
                self._exchange_clear_selection()
                return None

        indices = [index for index, _, _ in cards]
        for _ in self.loop(timeout=3):
            counts = read_fish_counts(self.device.image, indices)
            _, gain = read_fish_meat(self.device.image)
            if counts == [amounts[fish_id] for _, fish_id, _ in cards] and gain == expected:
                break
        else:
            logger.warning(f'Fish selection {counts} gaining {gain} does not match planned exchange {amounts}')
            self._exchange_clear_selection()
            return None

        after = self._exchange_confirm(meat_id, before, expected)
        if after is None:
            return None
        return FishMeatExchange(before, after, stock)

    def _exchange_confirm(self, meat_id, before, expected):
        """
        Confirm the selected fish, dismiss the item popup and verify the fish meat.

        Args:
            meat_id (int):
            before (int): Fish meat owned before the exchange.
            expected (int): Fish meat gain of the selected fish.

        Returns:
            int: Fish meat owned after the exchange, None if completion is not seen.
        """
        popup_confirmed = False
        items_received = False
        owned = before
        for _ in self.loop(timeout=10):
            if self.handle_island_get_items():
                items_received = True
                continue
            if self.handle_island_level_up():
                continue
            if self.handle_island_popup_confirm('EXCHANGE'):
                popup_confirmed = True
                continue
            owned, gain = read_fish_meat(self.device.image)
            # Exact match only. While the popup fades, the dimmed gain digits may read
            # as part of the owned digits, e.g. 13052 +24 as 1305224.
            if items_received and gain == 0 and owned == before + expected:
                return owned
            # The page takes a while to update after the popup is confirmed
            if not popup_confirmed and not items_received and self.appear_then_click(
                    ISLAND_EXCHANGE_CONFIRM, offset=(20, 20), interval=2):
                continue
        logger.warning(f'Exchange expected {expected} {item_name_with_id(meat_id)}, '
                       f'but owned {owned} from {before}, item popup handled: {items_received}')
        return None

    def island_shop_exchange(self, require_dict={}, keep=None):
        """
        Args:
            require_dict (dict): {fish meat id: least amount to gain}.
            keep (dict): {fish id: amount} not to exchange, None to exchange all fish.

        Returns:
            bool: If every fish meat gained at least its required amount.
        """
        success = True
        for meat_id, require in require_dict.items():
            result = self.island_exchange_fish_meat(meat_id, keep=keep)
            success = result is not None and result.after - result.before >= require and success
        return success

    def island_shop_exchange_all_fish_meat(self, keep=None):
        """Exchange all available freshwater and saltwater fish above keep in one visit."""
        return self.island_shop_exchange({2521: 0, 2522: 0}, keep=keep)
