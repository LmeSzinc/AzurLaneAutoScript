"""
Island transport commissions.

Scan the three primary slots and commission list, let TransportOptimizer choose
commissions to submit, swap selected list commissions into unchosen primary slots,
and submit the selected slots. Preserve worthwhile jobs in idle primary slots
before refreshing an unproductive list.
"""
import os
from datetime import datetime, timedelta

import cv2
import numpy as np

import module.config.server as server
from module.base.button import Button, ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import (
    area_offset,
    crop,
    get_color,
    load_image,
    random_rectangle_vector_opted,
    rgb2luma,
)
from module.island.assets import *
from module.island.data import DIC_ISLAND_ITEM
from module.island.utils import get_order_effective_stock, load_hard_floor_items, normalize_item_keys
from module.island_handler.exchange import IslandExchange
from module.island_handler.production_planner import create_production_problem
from module.island_handler.recipe import IslandReversedDigitCounter
from module.island_handler.restaurant_config import get_menu_reserve_items
from module.island_handler.transport_optimizer import TransportCommission, TransportOptimizer
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter, Duration
from module.ui.navbar import Navbar
from module.ui.page import page_island, page_island_transport
from module.ui.switch import Switch

SLOT_COUNT = 3
SLOT_DELTA = 175
TEXT_BLUE = (57, 190, 255)
TEXT_RED = (244, 124, 124)
BAR_ORANGE = (248, 180, 76)
EMPTY_GREY = (211, 211, 211)
BADGE_DARK = (76, 80, 84)
ROW_SELECTED = (187, 220, 236)
# A selected list row is blended with this blue: selected = (1 - alpha) * original + alpha * ROW_MASK
ROW_MASK = (56, 177, 236)
ROW_PLAIN = (230, 230, 230)
FISH_MEAT = (2521, 2522)
# Counters like 30001/15 still fit when read from the gap, so a stock spilling over the gap has at least 5 digits
SPILLED_STOCK = 10000

# Primary slots, one row per slot
BAR_GRID = ButtonGrid(
    origin=(455, 208), delta=(0, SLOT_DELTA), button_shape=(657, 26), grid_shape=(1, SLOT_COUNT),
    name='TRANSPORT_BAR')
TIMER_GRID = ButtonGrid(
    origin=(745, 207), delta=(0, SLOT_DELTA), button_shape=(105, 28), grid_shape=(1, SLOT_COUNT),
    name='TRANSPORT_TIMER')
# Item cards, 3 per slot, icon part only
SUBMISSION_GRID = ButtonGrid(
    origin=(481, 174), delta=(104.5, SLOT_DELTA), button_shape=(86, 64), grid_shape=(3, SLOT_COUNT),
    name='TRANSPORT_SUBMISSION')
REWARD_GRID = ButtonGrid(
    origin=(501, 182), delta=(101, SLOT_DELTA), button_shape=(80, 64), grid_shape=(3, SLOT_COUNT),
    name='TRANSPORT_REWARD')
# List popup
LIST_AREA = (400, 150, 900, 580)
LIST_DRAG_AREA = (750, 170, 890, 560)
LIST_SUBMISSION_X = (490, 578, 665)
LIST_REWARD_X = (486, 574, 661)
REFRESH_TIMER_AREA = (722, 86, 810, 114)
REFRESH_COOLDOWN = timedelta(hours=4)
REFRESH_RETRY = timedelta(minutes=15)
REFRESH_STORAGE = 'IslandTransport.Storage.Storage.RefreshAvailableAt'


class TransportViewSwitch(Switch):
    def handle_additional(self, main):
        return main.handle_transport_popup()


# Toggle between commission contents and rewards, it shows the label of the view it switches to
TRANSPORT_VIEW = TransportViewSwitch('Transport_view', offset=(10, 10))
TRANSPORT_VIEW.add_state('content', check_button=ISLAND_TRANSPORT_VIEW_REWARD)
TRANSPORT_VIEW.add_state('reward', check_button=ISLAND_TRANSPORT_VIEW_CONTENT)

def counter_dy():
    return 6 if server.server == 'en' else 0

def primary_counter_area(card, slot):
    """
    `stock/need` text under a submission card, right aligned at x + 82.
    Long stocks spill left, so start in the gap, after the text of the previous card.
    """
    x = SUBMISSION_GRID[card, slot].area[0]
    left = SUBMISSION_GRID[card - 1, slot].area[0] + 85 if card else x - 20
    dy = counter_dy()
    return left, 239 + dy + SLOT_DELTA * slot, x + 84, 255 + dy + SLOT_DELTA * slot


def adjust_counter(stock, need, spilled=False, covered=False):
    """
    Args:
        stock (int):
        need (int):
        spilled (bool): If the stock spills over the gap, its leading digits are cut off.
        covered (bool): If the spilled stock of the next card covers the last digit of need.

    Returns:
        tuple[int, int]: (stock, need), stock is a lower bound.
    """
    if covered:
        # Take the covered digit as its largest value
        need = need // 10 * 10 + 9
    if spilled:
        stock = max(stock, SPILLED_STOCK)
    return stock, need


def primary_badge_area(card, slot):
    x, y = REWARD_GRID[card, slot].area[:2]
    return x + 40, y + 64, x + 79, y + 82


def remove_row_mask(image, row):
    """
    Restore the colours of a selected list row. alpha is measured on the plain background right of the
    cards, so a mask still fading in is removed too. Red separates the mask from the background best.

    Args:
        image (np.ndarray): Screenshot.
        row (ListRow):

    Returns:
        np.ndarray: A copy of the screenshot with the row restored.
    """
    red = get_color(image, row.select_area)[0]
    alpha = np.clip((ROW_PLAIN[0] - red) / (ROW_PLAIN[0] - ROW_MASK[0]), 0, 0.5)
    x1, y1, x2, y2 = row.area
    region = image[y1:y2, x1:x2].astype(np.float32)
    region = (region - alpha * np.array(ROW_MASK, dtype=np.float32)) / (1 - alpha)
    image = image.copy()
    image[y1:y2, x1:x2] = np.clip(np.round(region), 0, 255).astype(np.uint8)
    return image


def assign_swaps(ready_slots, chosen_slots, chosen_subs, blocked_slots, empty_slots=()):
    """
    Args:
        ready_slots (list[int]): Idle primary slots available for the selection.
        chosen_slots (list[int]): Ready slots whose own commission is chosen.
        chosen_subs (list): Chosen list commissions.
        blocked_slots (list[int]): Ready slots whose commission can't be submitted now.
        empty_slots (list[int]): Empty primary slots, filled before occupied ones.

    Returns:
        list[tuple[int, Any]]: (slot, list commission) pairs. Each chosen list commission
            replaces a primary commission that is not chosen, empty and blocked slots first.
    """
    free = [slot for slot in ready_slots if slot not in chosen_slots]
    free.sort(key=lambda slot: (slot not in empty_slots, slot not in blocked_slots, slot))
    if len(chosen_subs) > len(free):
        logger.warning(f'{len(chosen_subs)} list commissions chosen but only {len(free)} slots to swap into')
    return list(zip(free, chosen_subs))


class TransportBadgeOcr(Digit):
    """White count in a dark badge, which fills the crop. azur_lane_jp needs some margin above and below."""

    def pre_process(self, image):
        image = super().pre_process(image)
        return cv2.copyMakeBorder(image, 2, 4, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))


class TransportItemMatcher:
    """
    Recognise item cards with the templates in assets/island/transport, resized per view.

    *_2.png are 46x46 icons from recipe cards or item details. Unnumbered files are
    73x56 crops of primary submission cards, used with the card background trimmed
    for items without a recipe icon (Copper Ore, fish meats, Poultry).
    """
    FOLDER = './assets/island/transport'
    # Scales are measured on screenshots, matching gets much worse a few percent off.
    # Scales of *_2.png
    ICON_SCALE = {
        'primary_submission': 1.045,
        'list_submission': 0.835,
        'primary_reward': 0.83,
        'list_reward': 0.715,
    }
    # Scales of unnumbered files. Reward views draw these icons a bit smaller than ICON_SCALE suggests
    CARD_SCALE = {
        'primary_submission': 1.,
        'list_submission': 0.795,
        'primary_reward': 0.78,
        'list_reward': 0.665,
    }
    SIMILARITY = 0.70
    COLOR_THRESHOLD = 20
    CARD_WHITE = (237, 237, 235)

    def __init__(self):
        self._templates = {}

    @cached_property
    def sources(self):
        icons, cards = {}, {}
        for file in sorted(os.listdir(self.FOLDER)):
            name, ext = os.path.splitext(file)
            if ext != '.png':
                continue
            image = load_image(os.path.join(self.FOLDER, file))
            if name.endswith('_2'):
                icons[name[:-2]] = image
            else:
                cards[name] = image
        return icons, cards

    @cached_property
    def item_ids(self):
        return {
            data['name']['en'].replace(' ', '_'): item_id
            for item_id, data in DIC_ISLAND_ITEM.items()
        }

    def card_icon(self, image):
        diff = np.abs(image.astype(int) - np.array(self.CARD_WHITE)).max(axis=2) > 25
        ys, xs = np.where(diff)
        return image[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

    def templates(self, view):
        """
        Returns:
            dict: {name: (image, luma image, mean color)}
        """
        if view not in self._templates:
            icons, cards = self.sources
            out = {}
            for name, image in icons.items():
                scale = self.ICON_SCALE[view]
                out[name] = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            for name, image in cards.items():
                if name not in out:
                    scale = self.CARD_SCALE[view]
                    out[name] = cv2.resize(self.card_icon(image), None, fx=scale, fy=scale,
                                           interpolation=cv2.INTER_AREA)
            self._templates[view] = {
                name: (image, rgb2luma(image), tuple(cv2.mean(image)[:3]))
                for name, image in out.items()
            }
        return self._templates[view]

    def match(self, image, area, view):
        """
        Args:
            image (np.ndarray): Screenshot.
            area (tuple): Card area to search the icon in.
            view (str): Key of ICON_SCALE.

        Returns:
            int: Item id, None if no template matches.
        """
        x1, y1, x2, y2 = area
        passed = []
        for name, (template, luma, color) in self.templates(view).items():
            th, tw = template.shape[:2]
            if tw > x2 - x1 or th > y2 - y1:
                continue
            button = Button(area=(x1, y1, x1 + tw, y1 + th), color=color, button=(x1, y1, x1 + tw, y1 + th),
                            name=f'TRANSPORT_ITEM_{name}')
            button.image, button.image_luma = template, luma
            button._match_init = button._match_luma_init = True
            if button.match_template_color(image, offset=(0, 0, x2 - x1 - tw, y2 - y1 - th),
                                           similarity=self.SIMILARITY, threshold=self.COLOR_THRESHOLD):
                passed.append(name)
        if not passed:
            return None
        if len(passed) > 1:
            card = rgb2luma(crop(image, area))
            scores = {name: cv2.minMaxLoc(cv2.matchTemplate(card, self.templates(view)[name][1],
                                                            cv2.TM_CCOEFF_NORMED))[1]
                      for name in passed}
            passed = sorted(passed, key=lambda name: -scores[name])
            logger.info(f'Transport item ambiguous in {view}: '
                        + ', '.join(f'{name} {scores[name]:.3f}' for name in passed))
        return self.item_ids.get(passed[0])


class TransportRewards(dict):
    """Recognised rewards, with incomplete OCR kept distinct from an empty reward."""
    unknown = False


class ScannedCommission:
    def __init__(self, name, slot=None, index=None):
        """
        Args:
            name (str): P1-P3 for primary slots, 01-06 for the list.
            slot (int): Primary slot, 0-2.
            index (int): List index, 1-6.
        """
        self.name = name
        self.slot = slot
        self.index = index
        self.submissions = []
        self.stock = {}
        self.rewards = TransportRewards()
        self.unknown = False
        self.empty = False
        self.remaining = 1

    def __repr__(self):
        submissions = ', '.join(
            f'{DIC_ISLAND_ITEM[item_id]["name"]["en"]} {self.stock.get(item_id, "?")}/{need}'
            for item_id, need in self.submissions)
        rewards = ', '.join(f'{DIC_ISLAND_ITEM[item_id]["name"]["en"]} x{count}'
                            for item_id, count in self.rewards.items())
        unknown = ' (unknown item)' if self.unknown else ''
        return f'{self.name}: [{submissions}] -> [{rewards}]{unknown}'

    @property
    def commission(self):
        return TransportCommission(self.submissions, self.rewards, name=self.name)


class ListRow:
    def __init__(self, anchor, index):
        self.anchor = anchor
        self.index = index
        self.top = anchor[1] - 26

    @property
    def area(self):
        return LIST_AREA[0], self.top, LIST_AREA[2], self.top + 90

    @property
    def select_area(self):
        """Area right of the cards that selects the row without opening item details."""
        return 760, self.top + 10, 880, self.top + 80

    def submission_area(self, card):
        x = LIST_SUBMISSION_X[card]
        return x, self.top + 4, x + 73, self.top + 60

    def counter_area(self, card):
        """Right aligned at x + 68, starting in the gap like primary_counter_area."""
        x = LIST_SUBMISSION_X[card]
        left = LIST_SUBMISSION_X[card - 1] + 71 if card else x - 17
        return left, self.top + 58, x + 70, self.top + 76

    def reward_area(self, card):
        x = LIST_REWARD_X[card]
        return x, self.top + 2, x + 71, self.top + 62

    def badge_area(self, card):
        x = LIST_REWARD_X[card]
        return x + 31, self.top + 66, x + 70, self.top + 82


class IslandTransport(IslandExchange):
    next_run_time = None

    @cached_property
    def transport_item_matcher(self):
        return TransportItemMatcher()

    @cached_property
    def transport_digit_lang(self):
        # 'azur_lane' is the azur_lane_jp model on JP, see Ocr.__init__
        if server.server == 'jp':
            return 'azur_lane'
        return 'cnocr'

    @cached_property
    def transport_slot_counter_grid(self):
        if server.server == 'jp':
            origin, shape = (1070, 136), (29, 21)
        elif server.server == 'en':
            origin, shape = (1073, 136), (29, 22)
        else:
            origin, shape = (1074, 136), (28, 22)
        return ButtonGrid(origin=origin, delta=(0, SLOT_DELTA), button_shape=shape,
                          grid_shape=(1, SLOT_COUNT), name='TRANSPORT_SLOT_COUNTER')

    @cached_property
    def transport_counter_ocr(self):
        # `stock/need`, blue when covered and red when short
        if server.server == 'jp':
            threshold, sub_threshold = 200, 200
        elif server.server == 'en':
            # 90-160 all read the '/' correctly on EN; pick the middle of that window
            threshold, sub_threshold = 125, 110
        else:
            # cnocr, tuned on CN, which draws thinner digits
            threshold, sub_threshold = 170, 110
        return IslandReversedDigitCounter([], lang=self.transport_digit_lang, letter=TEXT_BLUE, sub_letter=TEXT_RED,
                                          threshold=threshold, sub_threshold=sub_threshold,
                                          alphabet='0123456789/IDSB', name='TRANSPORT_COUNTER_OCR')

    @cached_property
    def transport_slot_counter_ocr(self):
        # Remaining trips / limit, independent of whether Submit All is enabled.
        return DigitCounter([], lang=self.transport_digit_lang, letter=BADGE_DARK, threshold=128,
                            name='TRANSPORT_SLOT_COUNTER_OCR')

    @cached_property
    def transport_badge_ocr(self):
        #EN badge background artifact reads as 7 at threshold 160
        if server.server == 'en':
            threshold = 140
        else:
            threshold = 160
        return TransportBadgeOcr([], lang=self.transport_digit_lang, letter=(255, 255, 255), threshold=threshold,
                                name='TRANSPORT_REWARD_OCR')

    @cached_property
    def transport_index_ocr(self):
        return Digit([], lang=self.transport_digit_lang, letter=(60, 60, 60), threshold=128,
                     name='TRANSPORT_INDEX_OCR')

    @cached_property
    def transport_timer_ocr(self):
        return Duration([], lang=self.transport_digit_lang, letter=(255, 255, 255), threshold=128,
                        name='TRANSPORT_TIMER_OCR')

    @cached_property
    def transport_refresh_timer_ocr(self):
        return Duration(REFRESH_TIMER_AREA, lang=self.transport_digit_lang, letter=BADGE_DARK, threshold=128,
                        name='TRANSPORT_REFRESH_TIMER_OCR')

    @cached_property
    def hard_floor(self):
        return normalize_item_keys(load_hard_floor_items(
            self.config.cross_get("IslandProduction.IslandProduction.HardFloorItems", "")
        ))

    @cached_property
    def reserve(self):
        return get_menu_reserve_items(self.config)

    # Detection

    def slot_appear(self, button, slot, interval=0):
        """
        Match a slot-1 asset in another slot, `Button.move` copies would template-match a black crop.
        Clicking the button right after it appears clicks it in that slot.
        """
        offset = (-5, SLOT_DELTA * slot - 10, 5, SLOT_DELTA * slot + 10)
        return self.match_template_color(button, offset=offset, interval=interval)

    def slot_running(self, slot):
        return self.image_color_count(BAR_GRID[0, slot], color=BAR_ORANGE, threshold=30, count=3000)

    def slot_empty(self, slot):
        # The first item-card area is entirely grey only in the empty placeholder.
        # This background is shared by the server layouts and avoids matching translated text.
        return self.image_color_count(SUBMISSION_GRID[0, slot], color=EMPTY_GREY, threshold=12, count=5000)

    def transport_slot_counters(self):
        # DigitCounter reads one counter at a time and returns current, remain, total.
        return [self.transport_slot_counter_ocr.ocr([crop(self.device.image, button.area)], direct_ocr=True)
                for button in self.transport_slot_counter_grid.buttons]

    def transport_slot_states(self, counters=None):
        """
        Returns:
            list[str]: 'completed', 'running', 'empty', 'ready', 'exhausted' or 'other' (unreadable).
                Empty slots still need a positive trip counter to run a new commission.
        """
        if counters is None:
            counters = self.transport_slot_counters()
        states = []
        for slot, (remaining, _, limit) in enumerate(counters):
            if self.slot_appear(ISLAND_TRANSPORT_CLAIM, slot):
                states.append('completed')
            elif self.slot_running(slot):
                states.append('running')
            elif 0 <= remaining <= limit and limit > 0 and self.slot_empty(slot):
                states.append('empty')
            elif 0 < remaining <= limit:
                states.append('ready')
            elif remaining == 0 < limit and self.slot_appear(ISLAND_TRANSPORT_SWAP, slot):
                states.append('exhausted')
            else:
                states.append('other')
        return states

    def is_in_transport_main(self):
        return self.ui_page_appear(page_island_transport, offset=(20, 20))

    def handle_transport_popup(self):
        if self.appear_then_click(ISLAND_TRANSPORT_DETAIL_CLOSE, offset=(20, 20), interval=2):
            return True
        if self.handle_island_additional():
            return True
        if self.appear(ISLAND_ORDER_LEVEL_UP, offset=(20, 20), interval=1):
            logger.info('Detected island level up')
            self.device.click(ISLAND_CLICK_SAFE_AREA)
            return True
        return False

    # Reading cards

    def read_submissions(self, cards, image=None):
        """
        Args:
            cards (list[tuple]): (card area, counter area, view)
            image (np.ndarray): Screenshot, the current one if None.

        Returns:
            tuple[list, dict, bool]: [(item_id, need)], {item_id: stock}, has unknown item
        """
        if image is None:
            image = self.device.image
        # CN draws thinner digits, which have fewer pixels close to the text colour
        present = [card for card in cards
                   if self.image_color_count(crop(image, card[1], copy=False), color=TEXT_BLUE, threshold=60, count=20)
                   or self.image_color_count(crop(image, card[1], copy=False), color=TEXT_RED, threshold=60, count=20)]
        if not present:
            return [], {}, False
        counters = self.transport_counter_ocr.ocr(
            [crop(image, counter) for _, counter, _ in present], direct_ocr=True)
        submissions, stock, unknown = [], {}, False
        for (area, counter, view), (current, need, _) in zip(present, counters):
            x1, y1, x2, y2 = counter
            # Text at the left edge is a stock spilling over the gap,
            # text right of it is the spilled stock of the next card
            spilled = self.counter_text_appear(image, (x1, y1, x1 + 2, y2))
            covered = self.counter_text_appear(image, (x2 + 2, y1, x2 + 6, y2))
            current, need = adjust_counter(current, need, spilled=spilled, covered=covered)
            item_id = self.transport_item_matcher.match(image, area, view)
            if item_id is None or need <= 0:
                if item_id is None:
                    logger.warning(f'Unknown transport item in {view}')
                else:
                    logger.warning(f'Unable to read the counter of {DIC_ISLAND_ITEM[item_id]["name"]["en"]}')
                unknown = True
                continue
            if spilled or covered:
                logger.info(f'Counter of {DIC_ISLAND_ITEM[item_id]["name"]["en"]} read as {current}/{need}, '
                            f'spilled={spilled}, covered={covered}')
            submissions.append((item_id, need))
            stock[item_id] = max(stock.get(item_id, 0), current)
        return submissions, stock, unknown

    def counter_text_appear(self, image, area):
        """If counter text is in a gap between cards, including faint edges of thin strokes."""
        image = crop(image, area, copy=False)
        return self.image_color_count(image, color=TEXT_BLUE, threshold=75, count=1) \
            or self.image_color_count(image, color=TEXT_RED, threshold=60, count=1)

    def read_rewards(self, cards, image=None):
        """
        Args:
            cards (list[tuple]): (card area, badge area, view)
            image (np.ndarray): Screenshot, the current one if None.

        Returns:
            dict: {item_id: count}, unknown rewards are left out
        """
        if image is None:
            image = self.device.image
        present = [card for card in cards
                   if self.image_color_count(crop(image, card[1], copy=False), color=BADGE_DARK, threshold=20, count=150)]
        rewards = TransportRewards()
        if not present:
            rewards.unknown = True
            return rewards
        counts = self.transport_badge_ocr.ocr(
            [crop(image, badge) for _, badge, _ in present], direct_ocr=True)
        for (area, _, view), count in zip(present, counts):
            item_id = self.transport_item_matcher.match(image, area, view)
            if item_id is None:
                logger.info(f'Unknown transport reward item in {view} is left out')
                rewards.unknown = True
                continue
            if count > 0:
                rewards[item_id] = rewards.get(item_id, 0) + count
            else:
                rewards.unknown = True
        return rewards

    # Primary slots

    def transport_claim_rewards(self, skip_first_screenshot=True):
        """Claim every completed slot."""
        logger.hr('Transport claim rewards', level=2)
        confirm = Timer(1.5, count=3).start()
        for _ in self.loop(skip_first=skip_first_screenshot, timeout=30):
            if self.handle_transport_popup():
                confirm.reset()
                continue
            if not self.is_in_transport_main():
                confirm.reset()
                continue
            completed = [slot for slot in range(SLOT_COUNT) if self.slot_appear(ISLAND_TRANSPORT_CLAIM, slot)]
            if completed:
                confirm.reset()
                if self.slot_appear(ISLAND_TRANSPORT_CLAIM, completed[0], interval=2):
                    logger.info(f'Claim transport reward of P{completed[0] + 1}')
                    self.device.click(ISLAND_TRANSPORT_CLAIM)
                continue
            if confirm.reached():
                return True
        logger.warning('Transport claim rewards timeout')
        return False

    def transport_scan_slots(self, rewards=True):
        """
        Args:
            rewards (bool): Whether to switch to the rewards view and read rewards.

        Returns:
            tuple[list[str], dict[int, ScannedCommission]]: Slot states and idle primary slots,
                including empty slots and occupied slots with no trips remaining.
        """
        logger.hr('Transport scan primary slots', level=3)
        TRANSPORT_VIEW.set('content', main=self)
        self.device.screenshot()
        counters = self.transport_slot_counters()
        states = self.transport_slot_states(counters)
        slots = {slot: ScannedCommission(f'P{slot + 1}', slot=slot)
                 for slot, state in enumerate(states) if state in ('ready', 'empty', 'exhausted')}
        for slot, scanned in slots.items():
            remaining, _, limit = counters[slot]
            scanned.remaining = remaining if 0 <= remaining <= limit and limit > 0 else 0
            scanned.empty = states[slot] == 'empty'
            if scanned.empty:
                continue
            cards = [(SUBMISSION_GRID[card, slot].area, primary_counter_area(card, slot), 'primary_submission')
                     for card in range(3)]
            scanned.submissions, scanned.stock, scanned.unknown = self.read_submissions(cards)
            scanned.unknown |= not scanned.submissions
        if rewards and slots:
            TRANSPORT_VIEW.set('reward', main=self)
            self.device.screenshot()
            for slot, scanned in slots.items():
                if scanned.empty:
                    continue
                cards = [(REWARD_GRID[card, slot].area, primary_badge_area(card, slot), 'primary_reward')
                         for card in range(3)]
                scanned.rewards = self.read_rewards(cards)
            TRANSPORT_VIEW.set('content', main=self)
        logger.attr('TransportSlots', states)
        return states, slots

    # Sub-commission list

    def transport_list_open(self, slot=None, skip_first_screenshot=True):
        """
        Args:
            slot (int): Open this slot's swap list, or the commission list if None.
        """
        for _ in self.loop(skip_first=skip_first_screenshot, timeout=15):
            if self.appear(ISLAND_TRANSPORT_LIST_CHECK, offset=(20, 20)):
                return True
            if self.handle_transport_popup():
                continue
            if not self.is_in_transport_main():
                continue
            if slot is None:
                if self.appear_then_click(ISLAND_TRANSPORT_LIST_ENTER, offset=(20, 20), interval=2):
                    continue
            elif self.slot_empty(slot):
                self.device.click(BAR_GRID[0, slot])
            elif self.slot_appear(ISLAND_TRANSPORT_SWAP, slot, interval=2):
                self.device.click(ISLAND_TRANSPORT_SWAP)
                continue
        logger.warning('Failed to open transport list')
        return False

    def transport_list_close(self, skip_first_screenshot=True):
        for _ in self.loop(skip_first=skip_first_screenshot, timeout=15):
            if self.is_in_transport_main():
                return True
            if self.appear_then_click(ISLAND_TRANSPORT_DETAIL_CLOSE, offset=(20, 20), interval=2):
                continue
            if self.appear_then_click(ISLAND_TRANSPORT_LIST_BACK, offset=(20, 20), interval=2):
                continue
        logger.warning('Failed to close transport list')
        return False

    @cached_property
    def _transport_list_side_navbar(self):
        transport_list_side_navbar = ButtonGrid(
            origin=(320, 90), delta=(0, 170),
            button_shape=(58, 142), grid_shape=(1, 2),
            name='TRANSPORT_LIST_SIDE_NAVBAR'
        )
        # Active tab is white with orange text, inactive tab is dark grey
        return Navbar(grids=transport_list_side_navbar,
                      active_color=(248, 180, 76),
                      inactive_color=(57, 57, 57),
                      active_threshold=30,
                      inactive_threshold=20,
                      active_count=500,
                      inactive_count=3000)

    def transport_list_side_navbar_ensure(self, upper=1):
        """
        The list remembers its last tab, so set it every time.

        Args:
            upper (int): 1 for required items, 2 for rewards.
        """
        return self._transport_list_side_navbar.set(self, upper=upper)

    def transport_list_rows(self):
        """
        Returns:
            list[ListRow]: Fully visible rows, top to bottom.
        """
        image = crop(self.device.image, LIST_AREA, copy=False)
        anchors = TEMPLATE_ISLAND_TRANSPORT_LIST_ANCHOR.match_multi(image, similarity=0.85, threshold=5)
        anchors = sorted((area_offset(anchor.area, offset=LIST_AREA[:2]) for anchor in anchors), key=lambda a: a[1])
        anchors = [anchor for anchor in anchors if anchor[1] - 26 >= 160 and anchor[1] + 62 <= LIST_AREA[3]]
        if not anchors:
            return []
        indices = self.transport_index_ocr.ocr(
            [crop(self.device.image, (a[0] - 30, a[1] + 5, a[0], a[1] + 29)) for a in anchors], direct_ocr=True)
        return [ListRow(anchor, index) for anchor, index in zip(anchors, indices) if 1 <= index <= 6]

    def transport_row_selected(self, row):
        return self.image_color_count(row.select_area, color=ROW_SELECTED, threshold=15, count=3000)

    def transport_list_wait_rows(self, skip_first_screenshot=False):
        """
        Take screenshots until the list stops moving.

        Returns:
            list[ListRow]:
        """
        last = None
        for _ in self.loop(skip_first=skip_first_screenshot, timeout=3):
            rows = self.transport_list_rows()
            current = [(row.index, row.top) for row in rows]
            if current == last:
                return rows
            last = current
        logger.warning('Transport list is still moving')
        return self.transport_list_rows()

    def transport_list_drag(self, down=True):
        """
        Args:
            down (bool): True to move the list content up and see later rows.

        Returns:
            list[ListRow]: Rows after the drag.
        """
        vector = (0, -300) if down else (0, 300)
        p1, p2 = random_rectangle_vector_opted(vector, box=LIST_DRAG_AREA, padding=0)
        self.device.drag(p1, p2, hold_duration=0.1, name='TRANSPORT_LIST_DRAG')
        return self.transport_list_wait_rows()

    def transport_list_top(self):
        """
        Returns:
            list[ListRow]: Rows at the top of the list, indices may have gaps.
        """
        rows = self.transport_list_wait_rows()
        for _ in range(3):
            if not rows or rows[0].index == 1:
                break
            first = rows[0].index
            rows = self.transport_list_drag(down=False)
            if rows and rows[0].index == first:
                break
        return rows

    def transport_list_select(self, index, skip_first_screenshot=True):
        """
        Click a visible row until it gets the selected blue mask. The click goes right of the cards,
        clicking a card would open its item details.

        Returns:
            list[ListRow]: Rows after selecting, None if failed.
        """
        click_timer = Timer(2, count=3)
        for _ in self.loop(skip_first=skip_first_screenshot, timeout=5):
            if self.appear_then_click(ISLAND_TRANSPORT_DETAIL_CLOSE, offset=(20, 20), interval=2):
                continue
            rows = self.transport_list_rows()
            row = next((row for row in rows if row.index == index), None)
            if row is None:
                continue
            if self.transport_row_selected(row):
                return rows
            if click_timer.reached_and_reset():
                self.device.click(Button(area=row.select_area, color=(), button=row.select_area,
                                         name=f'TRANSPORT_LIST_ROW_{index}'))
        logger.warning(f'Failed to select list commission {index:02d}')
        return None

    def transport_list_read_page(self, rows, rewards, image=None):
        """
        Args:
            rows (list[ListRow]):
            rewards (bool):
            image (np.ndarray): Screenshot, the current one if None.

        Returns:
            dict[int, Any]: {index: rewards} or {index: (submissions, stock, unknown)}
        """
        result = {}
        for row in rows:
            if rewards:
                cards = [(row.reward_area(card), row.badge_area(card), 'list_reward') for card in range(3)]
                result[row.index] = self.read_rewards(cards, image=image)
            else:
                cards = [(row.submission_area(card), row.counter_area(card), 'list_submission') for card in range(3)]
                result[row.index] = self.read_submissions(cards, image=image)
        return result

    def transport_list_read_selected(self, row, rewards):
        """Read a selected row with its blue mask removed."""
        image = remove_row_mask(self.device.image, row)
        return self.transport_list_read_page([row], rewards, image=image)

    def transport_list_read_untinted(self, rows, rewards):
        """
        The selected row has a blue mask which shifts item colours. Read the other rows first, then select
        another row and read the formerly selected one. If it is the only row, remove the mask instead.
        """
        selected = [row for row in rows if self.transport_row_selected(row)]
        others = [row for row in rows if row not in selected]
        result = self.transport_list_read_page(others, rewards)
        if selected:
            index = selected[0].index
            rows = self.transport_list_select(others[0].index) if others else None
            row = next((row for row in rows or [] if row.index == index), None)
            if row is not None and not self.transport_row_selected(row):
                result.update(self.transport_list_read_page([row], rewards))
            else:
                result.update(self.transport_list_read_selected(selected[0], rewards))
        return result

    def transport_list_read_tab(self, rewards):
        """
        Returns:
            dict[int, Any]: See transport_list_read_page.
        """
        if not self.transport_list_side_navbar_ensure(upper=2 if rewards else 1):
            return None
        rows = self.transport_list_top()
        if not rows:
            logger.warning('No transport list rows could be read')
            return None
        result = {}
        for _ in range(3):
            result.update(self.transport_list_read_untinted(rows, rewards))
            if not rows or rows[-1].index >= 6:
                break
            last = rows[-1].index
            rows = self.transport_list_drag(down=True)
            if not rows or rows[-1].index <= last:
                break
        return result

    def transport_scan_list(self):
        """
        Returns:
            dict[int, ScannedCommission] | None: List commissions by index, None on a failed scan.
        """
        logger.hr('Transport scan commission list', level=3)
        if not self.transport_list_open():
            return None
        self.transport_observe_refresh()
        submissions = self.transport_list_read_tab(rewards=False)
        rewards = self.transport_list_read_tab(rewards=True)
        closed = self.transport_list_close()
        if submissions is None or rewards is None or submissions.keys() != rewards.keys() or not closed:
            logger.warning('Incomplete transport list scan')
            return None
        subs = {}
        for index, (items, stock, unknown) in sorted(submissions.items()):
            scanned = ScannedCommission(f'{index:02d}', index=index)
            scanned.submissions, scanned.stock, scanned.unknown = items, stock, unknown
            scanned.unknown |= not items
            scanned.rewards = rewards.get(index, {})
            subs[index] = scanned
        return subs

    # Fish meat

    def needs_fish_meat(self, commissions, max_commissions):
        """
        Args:
            commissions (list[ScannedCommission]):
            max_commissions (int): How many commissions can be submitted, the number of ready slots.

        Returns:
            bool: If the effective stock of a fish meat is short of its largest needs
                in max_commissions commissions.
        """
        commissions = [scanned for scanned in commissions if not scanned.unknown]
        effective = self.transport_effective_stock(commissions)
        for item_id in FISH_MEAT:
            needs = sorted((sum(need for submitted, need in scanned.submissions if submitted == item_id)
                            for scanned in commissions), reverse=True)
            need = sum(needs[:max_commissions])
            available = max(effective.get(item_id, 0), 0)
            if need > available:
                logger.info(f'{DIC_ISLAND_ITEM[item_id]["name"]["en"]} effective stock {available} is short of {need} '
                            f'for {max_commissions} transport commissions')
                return True
        return False

    def transport_exchange_fish_meat(self):
        logger.hr('Transport exchange fish meat', level=2)
        self.ui_goto_island_shop()
        # Fish protected by hard floor, reserve and task target are kept
        if not self.island_shop_exchange_all_fish_meat(keep=self.get_fish_keep_items()):
            logger.info('Some fish could not be exchanged, continue with the fish meat in stock')
        self.ui_back(check_button=page_island.check_button)
        self.ui_goto(page_island_transport)

    # Decision

    def transport_effective_stock(self, commissions):
        stock = {}
        for scanned in commissions:
            for item_id, amount in scanned.stock.items():
                stock[item_id] = max(stock.get(item_id, 0), amount)
        return {
            item_id: get_order_effective_stock(
                amount, self.hard_floor.get(item_id, 0), reserve=self.reserve.get(item_id, 0))
            for item_id, amount in stock.items()
        }

    def transport_decide(self, slots, subs, preserve=False):
        """
        Args:
            preserve (bool): Choose jobs to protect in idle primaries, ignoring immediate stock.
                Spent trips provide parking space but never submission capacity.

        Returns:
            tuple[list, list]: [(slot, list commission)] swaps, [slot] selected.
                None means the board could not be valued; ([], []) is a valid empty plan.
        """
        mode = 'preservation' if preserve else 'submission'
        logger.hr(f'Transport calculate {mode} plan', level=2)
        if subs is None:
            return None
        ready = sorted(slot for slot, scanned in slots.items() if preserve or scanned.remaining > 0)
        if not ready:
            logger.info('No transport trips remain for submission')
            return [], []
        logger.info('Building transport production problem')
        problem = create_production_problem(self.config)
        if problem is None:
            return None
        candidates = [scanned for scanned in [slots[slot] for slot in ready] + list(subs.values())
                      if scanned.submissions and not scanned.unknown]
        effective = self.transport_effective_stock(list(slots.values()) + list(subs.values()))
        logger.info('Solving transport production baseline')
        optimizer = TransportOptimizer(problem, max_commissions=len(ready))
        logger.info(f'Selecting transport {mode} commissions: '
                    f'{len(candidates)} candidates, {len(ready)} slots')
        chosen = [candidates[index] for index in optimizer.select(
            [c.commission for c in candidates], None if preserve else effective)]
        if not optimizer.success:
            return None
        if not chosen:
            return [], []
        chosen_slots = [scanned.slot for scanned in chosen if scanned.slot is not None]
        chosen_subs = [scanned for scanned in chosen if scanned.index is not None]
        blocked = [slot for slot in ready
                   if slots[slot].unknown or any(need > max(effective.get(item_id, 0), 0)
                                                 for item_id, need in slots[slot].submissions)]
        swaps = assign_swaps(ready, chosen_slots, chosen_subs, blocked,
                             empty_slots=[slot for slot in ready if slots[slot].empty])
        submit = sorted(chosen_slots + [slot for slot, _ in swaps])
        logger.info(f'Transport {mode} plan: '
                    f'swap {[(f"P{slot + 1}", sub.name) for slot, sub in swaps]}, '
                    f'selected {[f"P{slot + 1}" for slot in submit]}')
        return swaps, submit

    def transport_refresh_reason(self, states, slots, subs, plan):
        """Return a refresh reason for unfilled primaries or trips on a recognised board."""
        if plan is None or subs is None or len(states) != SLOT_COUNT \
                or any(state in ('other', 'completed') for state in states):
            return None
        for scanned in list(slots.values()) + list(subs.values()):
            if not scanned.empty and (scanned.unknown or not scanned.submissions
                                      or not scanned.rewards or getattr(scanned.rewards, 'unknown', False)):
                logger.info('Skip transport refresh with incomplete commission recognition')
                return None
        selected = {slot for slot, _ in plan[0]}
        if any(scanned.empty and slot not in selected for slot, scanned in slots.items()):
            return 'Empty primary slots can be filled regardless of remaining trips'
        capacity = sum(scanned.remaining > 0 for scanned in slots.values())
        if len(plan[1]) < capacity:
            return 'Profitable, stocked commissions do not fill the remaining trips'
        return None

    # Actions

    def transport_refresh_status(self):
        """Read the list refresh control: ready, cooldown with remaining duration, or unknown."""
        if self.match_template_color(ISLAND_TRANSPORT_LIST_REFRESH, offset=(5, 5)):
            return 'ready', None
        if self.match_template_color(ISLAND_TRANSPORT_LIST_REFRESH_COOLDOWN, offset=(5, 5)):
            remain = self.transport_refresh_timer_ocr.ocr(self.device.image)
            if timedelta(0) < remain <= REFRESH_COOLDOWN:
                return 'cooldown', remain
        return 'unknown', None

    def transport_observe_refresh(self):
        """Remember the observed availability without writing config during a scan."""
        state, remain = self.transport_refresh_status()
        now = datetime.now()
        self.transport_refresh_time = (now + remain + timedelta(seconds=3) if state == 'cooldown'
                                       else now if state == 'ready' else None)
        return state

    def transport_load_refresh_time(self):
        value = self.config.cross_get(REFRESH_STORAGE, default='')
        try:
            return datetime.fromisoformat(value) if value else None
        except (TypeError, ValueError):
            logger.warning('Invalid saved transport refresh time')
            return None

    def transport_save_refresh_time(self, target):
        self.config.cross_set(REFRESH_STORAGE, target.isoformat(sep=' ') if target is not None else '')

    def transport_refresh_list(self):
        """
        Manually refresh list jobs and fill empty primaries, leaving occupied primaries intact.

        The game enforces a four-hour cooldown. Require the enabled control before clicking,
        then verify the cooldown appeared before reporting success. Rescan trip counters afterward.

        Returns:
            bool: Refresh verified and the primary view restored.
        """
        logger.hr('Transport refresh list', level=2)
        if not self.transport_list_open():
            return False
        state = self.transport_observe_refresh()
        if state != 'ready':
            if self.transport_refresh_time is not None:
                self.transport_save_refresh_time(self.transport_refresh_time)
            self.transport_list_close()
            return False

        self.device.click(ISLAND_TRANSPORT_LIST_REFRESH)
        # Retain the cooldown even if navigation fails after the game accepts the action.
        self.transport_save_refresh_time(datetime.now() + REFRESH_COOLDOWN)
        for _ in self.loop(skip_first=False, timeout=15):
            if self.handle_island_popup_confirm('TRANSPORT_REFRESH'):
                continue
            if self.handle_transport_popup():
                continue
            if self.appear(ISLAND_TRANSPORT_LIST_CHECK, offset=(20, 20)):
                if self.transport_observe_refresh() == 'cooldown':
                    self.transport_save_refresh_time(self.transport_refresh_time)
                    return self.transport_list_close()
            elif self.is_in_transport_main():
                if not self.transport_list_open():
                    break
        logger.warning('Transport refresh could not be verified')
        self.transport_list_close()
        return False

    def transport_list_locate(self, sub):
        """
        Scroll the list until a list commission is visible, and check that it still submits the same items.

        Returns:
            bool:
        """
        rows = self.transport_list_top()
        for _ in range(3):
            row = next((row for row in rows if row.index == sub.index), None)
            if row is not None:
                if self.transport_row_selected(row):
                    items, _, _ = self.transport_list_read_selected(row, rewards=False)[row.index]
                else:
                    items, _, _ = self.transport_list_read_page([row], rewards=False)[row.index]
                if sorted(items) != sorted(sub.submissions):
                    logger.warning(f'List commission {sub.name} changed, now submits {items}')
                    return False
                return True
            if not rows or rows[-1].index >= sub.index:
                break
            last = rows[-1].index
            rows = self.transport_list_drag(down=True)
            if not rows or rows[-1].index <= last:
                break
        logger.warning(f'List commission {sub.name} not found')
        return False

    def transport_swap(self, slot, sub):
        """
        Replace a slot's primary commission with a list commission, discarding the old one.
        Select a row in the slot's swap list, then confirm the selection and replacement prompt.

        Args:
            slot (int):
            sub (ScannedCommission):

        Returns:
            bool: If swap confirmed.
        """
        logger.hr(f'Transport swap P{slot + 1} <- {sub.name}', level=3)
        TRANSPORT_VIEW.set('content', main=self)
        empty = self.slot_empty(slot)
        if not empty and not self.slot_appear(ISLAND_TRANSPORT_SWAP, slot):
            logger.warning(f'No swap button on P{slot + 1}')
            return False
        if not self.transport_list_open(slot=slot):
            return False
        if not self.transport_list_side_navbar_ensure(upper=1) \
                or not self.transport_list_locate(sub) \
                or self.transport_list_select(sub.index) is None:
            self.transport_list_close()
            return False

        confirmed = False
        selected = False
        for _ in self.loop(timeout=15):
            if (confirmed or empty and selected) and self.is_in_transport_main():
                return True
            if self.handle_island_popup_confirm('TRANSPORT_SWAP'):
                confirmed = True
                continue
            if self.appear_then_click(ISLAND_TRANSPORT_DETAIL_CLOSE, offset=(20, 20), interval=2):
                continue
            if confirmed:
                # Never confirm the list twice, another row might be selected now
                if self.appear_then_click(ISLAND_TRANSPORT_LIST_BACK, offset=(20, 20), interval=2):
                    continue
            elif self.appear_then_click(ISLAND_TRANSPORT_LIST_CONFIRM, offset=(20, 20), interval=2):
                selected = True
                continue
        logger.warning('Transport swap timeout')
        self.transport_list_close()
        return False

    def transport_execute_plan(self, plan, submit=True):
        """Apply and verify swaps, then submit; return (any submitted, all actions succeeded)."""
        swaps, selected = plan
        if swaps:
            logger.hr('Transport swap commissions', level=2)
        for slot, sub in swaps:
            if not self.transport_swap(slot, sub):
                return False, False
        if swaps:
            _, rescanned = self.transport_scan_slots()
            for slot, sub in swaps:
                scanned = rescanned.get(slot)
                if scanned is None or scanned.unknown or sorted(scanned.submissions) != sorted(sub.submissions) \
                        or scanned.rewards != sub.rewards:
                    logger.warning(f'P{slot + 1} does not hold {sub.name} after swapping')
                    return False, False
                if submit and scanned.remaining <= 0:
                    logger.warning(f'P{slot + 1} has no remaining trips after selecting a commission')
                    return False, False
        submitted = False
        if submit:
            if selected:
                logger.hr('Transport submit commissions', level=2)
            for slot in selected:
                if not self.transport_submit(slot):
                    return submitted, False
                submitted = True
        return submitted, True

    def transport_submit(self, slot, skip_first_screenshot=True):
        """
        Submit all required items for a slot, handling item rewards and island level-up popups.

        Returns:
            bool: If the slot started running.
        """
        logger.hr(f'Transport submit P{slot + 1}', level=3)
        TRANSPORT_VIEW.set('content', main=self)
        confirm = Timer(2, count=4).start()
        for _ in self.loop(skip_first=skip_first_screenshot, timeout=30):
            if self.handle_transport_popup():
                confirm.reset()
                continue
            if not self.is_in_transport_main():
                confirm.reset()
                continue
            if self.slot_running(slot):
                if confirm.reached():
                    return True
                continue
            if self.slot_appear(ISLAND_TRANSPORT_SUBMIT, slot, interval=2):
                confirm.reset()
                self.device.click(ISLAND_TRANSPORT_SUBMIT)
                continue
        logger.warning(f'Transport submit P{slot + 1} timeout')
        return False

    def transport_next_run_time(self):
        """
        Returns:
            datetime: When all running transports finish, so rewards can be collected in one visit.
                None if none is running or no timer can be read.
        """
        TRANSPORT_VIEW.set('content', main=self)
        self.device.screenshot()
        running = [slot for slot in range(SLOT_COUNT) if self.slot_running(slot)]
        if not running:
            return None
        remains = self.transport_timer_ocr.ocr(
            [crop(self.device.image, TIMER_GRID[0, slot].area) for slot in running], direct_ocr=True)
        remains = [remain for remain in remains if remain.total_seconds() > 0]
        if not remains:
            return None
        return datetime.now() + max(remains)

    def transport_scan_board(self, exchange=True):
        """Read idle primaries and the list even when trips are spent; exchange fish for usable trips."""
        logger.hr('Transport scan commissions', level=2)
        states, slots = self.transport_scan_slots()
        capacity = sum(scanned.remaining > 0 for scanned in slots.values())
        subs = self.transport_scan_list() if slots else {}
        if exchange and capacity and subs is not None and self.needs_fish_meat(
                list(slots.values()) + list(subs.values()), max_commissions=capacity):
            self.transport_exchange_fish_meat()
            return self.transport_scan_board(exchange=False)
        for scanned in list(slots.values()) + list((subs or {}).values()):
            logger.info(f'Transport {scanned}')
        return states, slots, subs

    def run(self, dry_run=False):
        """
        Args:
            dry_run (bool): Scan and decide only, without claiming, exchanging, swapping or refreshing.

        Returns:
            datetime: Next batch collection, needed refresh or retry, or None for the next server reset.
        """
        if not self.server_support_island_transport():
            logger.info('Island transport is not available on this server')
            self.config.task_delay(server_update=True)
            return None
        self.ui_ensure(page_island_transport)
        claimed = dry_run or self.transport_claim_rewards()
        submitted = False
        failed = not claimed
        refresh_at = None
        # One initial pass, then at most one pass over the refreshed board.
        for cycle in range(2):
            states, slots, subs = self.transport_scan_board(exchange=not dry_run and claimed)
            plan = self.transport_decide(slots, subs)
            reason = self.transport_refresh_reason(states, slots, subs, plan)
            if dry_run or not claimed or plan is None:
                break
            started, success = self.transport_execute_plan(plan)
            submitted |= started
            if not success:
                failed = True
                break
            if reason is None:
                break

            if plan[0] or plan[1]:
                # Swaps change list membership; submissions consume stock. Park from a fresh scan.
                states, slots = self.transport_scan_slots()
                selected = {sub.index for _, sub in plan[0]}
                subs = {index: sub for index, sub in subs.items() if index not in selected}
                if subs:
                    subs = self.transport_scan_list()
            if self.transport_refresh_reason(states, slots, subs, ([], [])) is None:
                break
            preservation = self.transport_decide(slots, subs, preserve=True)
            if preservation is None:
                break
            _, success = self.transport_execute_plan(preservation, submit=False)
            if not success:
                failed = True
                break
            if preservation[0]:
                states, slots = self.transport_scan_slots()
                # Selecting a list job removes that index and does not consume stock.
                parked = {sub.index for _, sub in preservation[0]}
                subs = {index: sub for index, sub in subs.items() if index not in parked}
            reason = self.transport_refresh_reason(states, slots, subs, ([], []))
            if reason is None:
                break

            refresh_at = getattr(self, 'transport_refresh_time', None)
            if refresh_at is not None:
                self.transport_save_refresh_time(refresh_at)
            else:
                refresh_at = self.transport_load_refresh_time()
            if cycle or refresh_at is not None and refresh_at > datetime.now():
                break

            logger.info(f'Transport refresh requested: {reason}')
            if not self.transport_refresh_list():
                failed = True
                refresh_at = self.transport_load_refresh_time()
                break

        targets = [self.transport_next_run_time(), refresh_at]
        if failed:
            targets.append(datetime.now() + REFRESH_RETRY)
        targets = [target for target in targets if target is not None and target > datetime.now()]
        self.next_run_time = min(targets) if targets else None
        logger.info(f'Transport next run time: {self.next_run_time}')
        if self.next_run_time is not None:
            self.config.task_delay(target=self.next_run_time, server_update=True)
        else:
            self.config.task_delay(server_update=True)
        if submitted:
            # Submissions change item stock, check island orders again
            self.config.task_call('IslandOrder', force_call=False)
        return self.next_run_time

    def server_support_island_transport(self):
        return self.config.SERVER in ['cn', 'jp', 'en']
