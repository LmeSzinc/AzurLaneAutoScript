from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.equipment.equipment import Equipment
from module.logger import logger
from module.ocr.ocr import DigitCounter
from module.retire.assets import *
from module.ui.scroll import Scroll
from module.ui.switch import Switch

DOCK_SORTING = Switch("Dork_sorting")
DOCK_SORTING.add_status("Ascending", check_button=SORT_ASC, click_button=SORTING_CLICK)
DOCK_SORTING.add_status(
    "Descending", check_button=SORT_DESC, click_button=SORTING_CLICK
)

DOCK_FAVOURITE = Switch("Favourite_filter")
DOCK_FAVOURITE.add_status("on", check_button=COMMON_SHIP_FILTER_ENABLE)
DOCK_FAVOURITE.add_status("off", check_button=COMMON_SHIP_FILTER_DISABLE)

FILTER_SORT_GRIDS = ButtonGrid(
    origin=(284, 60),
    delta=(158, 0),
    button_shape=(137, 38),
    grid_shape=(6, 1),
    name="FILTER_SORT",
)
FILTER_SORT_TYPES = [
    ["rarity", "level", "total", "join", "intimacy", "stat"]
]  # stat has extra grid, not worth pursuing

FILTER_INDEX_GRIDS = ButtonGrid(
    origin=(284, 133),
    delta=(158, 57),
    button_shape=(137, 38),
    grid_shape=(6, 2),
    name="FILTER_INDEX",
)
FILTER_INDEX_TYPES = [
    ["all", "vanguard", "main", "dd", "cl", "ca"],
    ["bb", "cv", "repair", "ss", "others", "not_available"],
]

FILTER_FACTION_GRIDS = ButtonGrid(
    origin=(284, 267),
    delta=(158, 57),
    button_shape=(137, 38),
    grid_shape=(6, 2),
    name="FILTER_FACTION",
)
FILTER_FACTION_TYPES = [
    ["all", "eagle", "royal", "sakura", "iron", "dragon"],
    ["sardegna", "northern", "iris", "vichya", "other", "not_available"],
]

FILTER_RARITY_GRIDS = ButtonGrid(
    origin=(284, 400),
    delta=(158, 0),
    button_shape=(137, 38),
    grid_shape=(6, 1),
    name="FILTER_RARITY",
)
FILTER_RARITY_TYPES = [["all", "common", "rare", "elite", "super_rare", "ultra"]]

FILTER_EXTRA_GRIDS = ButtonGrid(
    origin=(284, 473),
    delta=(158, 57),
    button_shape=(137, 38),
    grid_shape=(6, 2),
    name="FILTER_EXTRA",
)
FILTER_EXTRA_TYPES = [
    [
        "no_limit",
        "has_skin",
        "can_retrofit",
        "enhanceable",
        "can_limit_break",
        "not_level_max",
    ],
    [
        "can_awaken",
        "can_awaken_plus",
        "special",
        "oath_skin",
        "not_available",
        "not_available",
    ],
]

CARD_GRIDS = ButtonGrid(
    origin=(93, 76),
    delta=(164 + 2 / 3, 227),
    button_shape=(138, 204),
    grid_shape=(7, 2),
    name="CARD",
)
CARD_RARITY_GRIDS = CARD_GRIDS.crop(area=(0, 0, 138, 5), name="RARITY")
CARD_LEVEL_GRIDS = CARD_GRIDS.crop(area=(77, 5, 138, 27), name="LEVEL")
CARD_EMOTION_GRIDS = CARD_GRIDS.crop(area=(23, 29, 48, 52), name="EMOTION")
CARD_BOTTOM_GRIDS = CARD_GRIDS.move(vector=(0, 94), name="CARD")
CARD_BOTTOM_LEVEL_GRIDS = CARD_LEVEL_GRIDS.move(vector=(0, 94), name="LEVEL")
CARD_BOTTOM_EMOTION_GRIDS = CARD_EMOTION_GRIDS.move(vector=(0, 94), name="EMOTION")
DOCK_SCROLL = Scroll(DOCK_SCROLL, color=(247, 211, 66), name="DOCK_SCROLL")

OCR_DOCK_SELECTED = DigitCounter(DOCK_SELECTED, threshold=64, name="OCR_DOCK_SELECTED")


class Dock(Equipment):
    def handle_dock_cards_loading(self):
        # Poor implementation.
        self.device.sleep((1, 1.5))
        self.device.screenshot()

    def dock_favourite_set(self, enable=False):
        if DOCK_FAVOURITE.set("on" if enable else "off", main=self):
            self.handle_dock_cards_loading()

    def _dock_quit_check_func(self):
        return not self.appear(DOCK_CHECK, offset=(20, 20))

    def dock_quit(self):
        self.ui_back(
            check_button=self._dock_quit_check_func, skip_first_screenshot=True
        )

    def dock_sort_method_dsc_set(self, enable=True):
        if DOCK_SORTING.set("Descending" if enable else "Ascending", main=self):
            self.handle_dock_cards_loading()

    def dock_filter_enter(self):
        self.ui_click(
            DOCK_FILTER,
            appear_button=DOCK_CHECK,
            check_button=DOCK_FILTER_CONFIRM,
            skip_first_screenshot=True,
        )

    def dock_filter_confirm(self):
        self.ui_click(
            DOCK_FILTER_CONFIRM, check_button=DOCK_CHECK, skip_first_screenshot=True
        )
        self.handle_dock_cards_loading()

    def dock_filter_set_execute(
        self,
        sort="level",
        index="all",
        faction="all",
        rarity="all",
        extra="no_limit",
        skip_first_screenshot=True,
    ):
        """
        A faster filter set function.

        Args:
            sort (str, list):
            index (str, list):
            faction (str, list):
            rarity (str, list):
            extra (str, list):
            skip_first_screenshot:

        Returns:
            bool: If success.

        Pages:
            in: DOCK_FILTER_CONFIRM
        """
        # [[button_1, need_enable_1], ...]
        list_filter = []
        for category in ["sort", "index", "faction", "rarity", "extra"]:
            require = locals()[category]
            require = require if isinstance(require, list) else [require]
            grids = globals()[f"FILTER_{category.upper()}_GRIDS"]
            names = globals()[f"FILTER_{category.upper()}_TYPES"]
            for x, y, button in grids.generate():
                name = names[y][x]
                list_filter.append([button, name in require])

        for _ in range(5):
            logger.info(
                f"Setting dock filter, sort={sort}, index={index}, faction={faction}, rarity={rarity}, extra={extra}"
            )
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            change_count = 0
            for button, enable in list_filter:
                active = self.image_color_count(
                    button, color=(181, 142, 90), threshold=235, count=250
                ) or self.image_color_count(
                    button, color=(74, 117, 189), threshold=235, count=250
                )
                if enable and not active:
                    self.device.click(button)
                    self.device.sleep((0.1, 0.2))
                    change_count += 1

            # End
            if change_count == 0:
                return True

        logger.warning(
            "Failed to set all dock filters after 5 trial, assuming current filters are correct."
        )
        return False

    def dock_filter_set(
        self, sort="level", index="all", faction="all", rarity="all", extra="no_limit"
    ):
        """
        A faster filter set function.

        Args:
            sort (str, list): ['rarity', 'level', 'total', 'join', 'intimacy', 'stat']
            index (str, list): [['all', 'vanguard', 'main', 'dd', 'cl', 'ca'],
                                ['bb', 'cv', 'repair', 'ss', 'others', 'not_available']]
            faction (str, list): [['all', 'eagle', 'royal', 'sakura', 'iron', 'dragon'],
                                  ['sardegna', 'northern', 'iris', 'vichya', 'other', 'not_available']]
            rarity (str, list): [['all', 'common', 'rare', 'elite', 'super_rare', 'ultra']]
            extra (str, list): [['no_limit', 'has_skin', 'can_retrofit', 'enhanceable', 'can_limit_break', 'not_level_max'],
                                ['can_awaken', 'can_awaken_plus', 'special', 'oath_skin', 'not_available', 'not_available']]

        Pages:
            in: page_dock
        """
        self.dock_filter_enter()
        self.dock_filter_set_execute()  # Reset filter
        self.dock_filter_set_execute(
            sort=sort, index=index, faction=faction, rarity=rarity, extra=extra
        )
        self.dock_filter_confirm()

    def dock_select_one(self, button, skip_first_screenshot=True):
        """
        Args:
            button (Button): Ship button to select
            skip_first_screenshot:
        """
        ocr_check_timer = Timer(1)

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(DOCK_CHECK, interval=2):
                self.device.click(button)

            if ocr_check_timer.reached():
                ocr_check_timer.reset()
                current, _, _ = OCR_DOCK_SELECTED.ocr(self.device.image)
                if current > 0:
                    break

    def dock_select_confirm(self, check_button, skip_first_screenshot=True):
        return self.ui_click(
            SHIP_CONFIRM,
            check_button=check_button,
            offset=(200, 50),
            skip_first_screenshot=skip_first_screenshot,
        )
