import cv2
import numpy as np
from scipy import signal
from module.base.button import Button, ButtonWrapper

from module.base.timer import Timer
from module.base.utils import area_size, crop, rgb2luma, load_image, crop
from module.logger import logger
from module.ui.scroll import Scroll
from tasks.base.assets.assets_base_popup import POPUP_CANCEL
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_support import COMBAT_SUPPORT_ADD, COMBAT_SUPPORT_LIST, \
    COMBAT_SUPPORT_LIST_SCROLL, COMBAT_SUPPORT_SELECTED, COMBAT_SUPPORT_LIST_GRID
from tasks.combat.assets.assets_combat_team import COMBAT_TEAM_SUPPORT, COMBAT_TEAM_DISMISSSUPPORT


def get_position_in_original_image(position_in_croped_image, crop_area):
    """
    Returns:
        tuple: (x, y) of position in original image
    """
    return (
        position_in_croped_image[0] + crop_area[0], position_in_croped_image[1] + crop_area[1]) if position_in_croped_image else None


class SupportCharacter:
    _image_cache = {}
    _crop_area = COMBAT_SUPPORT_LIST_GRID.matched_button.area

    def __init__(self, name, screenshot, similarity=0.85):
        self.name = name
        self.image = self._scale_character()
        self.screenshot = crop(screenshot, SupportCharacter._crop_area)
        self.similarity = similarity
        self.button = self._find_character()

    def __bool__(self):
        # __bool__ is called when use an object of the class in a boolean context
        return self.button is not None

    def __str__(self):
        return f'SupportCharacter({self.name})'

    __repr__ = __str__

    def _scale_character(self):
        """
        Returns:
            Image: Character image after scaled
        """

        if self.name in SupportCharacter._image_cache:
            logger.info(f"Using cached image of {self.name}")
            return SupportCharacter._image_cache[self.name]

        img = load_image(f"assets/character/{self.name}.png")
        scaled_img = cv2.resize(img, (85, 82))
        SupportCharacter._image_cache[self.name] = scaled_img
        logger.info(f"Character {self.name} image cached")
        return scaled_img

    def _find_character(self):
        character = np.array(self.image)
        support_list_img = self.screenshot
        res = cv2.matchTemplate(
            character, support_list_img, cv2.TM_CCOEFF_NORMED)

        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        max_loc = get_position_in_original_image(
            max_loc, SupportCharacter._crop_area)
        character_width = character.shape[1]
        character_height = character.shape[0]

        return (max_loc[0], max_loc[1], max_loc[0] + character_width, max_loc[1] + character_height) \
            if max_val >= self.similarity else None

    def selected_icon_search(self):
        """
        Returns:
            tuple: (x1, y1, x2, y2) of selected icon search area
        """
        return (
            self.button[0], self.button[1] - 5, self.button[0] + 30, self.button[1]) if self.button else None


class ArrowWrapper(ButtonWrapper):

    def find_center(self, image):
        res = cv2.matchTemplate(
            self.matched_button.image, image, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        return (
            (
                (max_loc[0] + self.matched_button.image.shape[1] / 2),
                (max_loc[1] + self.matched_button.image.shape[0] / 2),
            )
            if max_val > 0.75
            else None
        )


class NextSupportCharacter:
    _arrow = ArrowWrapper(
        name="NextSupportCharacterArrow",
        share=Button(
            file='./assets/support/selected_character_arrow.png',
            area=None,
            search=None,
            color=None,
            button=None,
        )
    )
    _crop_area = (290, 115, 435, 634)

    def __init__(self, screenshot):
        self.name = "SupportCharacterArrow"
        self.screenshot = crop(screenshot, NextSupportCharacter._crop_area)
        self.arrow_center = self._find_center()
        self.button = self._get_next_support_character_button()

    def __bool__(self):
        return self.button is not None

    def _find_center(self):
        center = NextSupportCharacter._arrow.find_center(self.screenshot)
        center = get_position_in_original_image(
            center, NextSupportCharacter._crop_area) if center else None
        return center

    def _get_next_support_character_button(self):
        area = (self.arrow_center[0] - 200, min(self.arrow_center[1] + 65, 615), self.arrow_center[0] + 10, min(
            self.arrow_center[1] + 80, 620)) if self.arrow_center and self.arrow_center[1] < 510 else None
        return ButtonWrapper(
            name="NextSupportCharacterButton",
            share=Button(
                file='./assets/support/selected_character_arrow.png',
                area=area,
                search=area,
                # if next support was selected, the average color of the button will larger than 220
                color=(220, 220, 220),
                button=area,
            )
        ) if self.arrow_center and self.arrow_center[1] < 510 else None


class SupportListScroll(Scroll):
    def cal_position(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            float: 0 to 1.
        """
        image = main.device.image

        temp_area = list(self.area)
        temp_area[0] = int(temp_area[0] * 0.98)
        temp_area[2] = int(temp_area[2] * 1.02)

        line = rgb2luma(crop(image, temp_area)).flatten()
        width = area_size(temp_area)[0]
        parameters = {
            "height": 180,
            "prominence": 30,
            "distance": width * 0.75,
        }
        peaks, _ = signal.find_peaks(line, **parameters)
        peaks //= width
        self.length = len(peaks)
        middle = np.mean(peaks)

        position = (middle - self.length / 2) / (self.total - self.length)
        position = position if position > 0 else 0.0
        position = position if position < 1 else 1.0
        logger.attr(
            self.name, f"{position:.2f} ({middle}-{self.length / 2})/({self.total}-{self.length})")
        return position


class CombatSupport(UI):
    def support_set(self, support_character_name: str = "FirstCharacter"):
        """
        Args:
            support_character_name: Support character name

        Returns:
            bool: If clicked

        Pages:
            in: COMBAT_PREPARE
            mid: COMBAT_SUPPORT_LIST
            out: COMBAT_PREPARE
        """
        logger.hr("Combat support")
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(COMBAT_TEAM_DISMISSSUPPORT):
                return True

            # Click
            if self.appear(COMBAT_TEAM_SUPPORT, interval=1):
                self.device.click(COMBAT_TEAM_SUPPORT)
                self.interval_reset(COMBAT_TEAM_SUPPORT)
                continue
            if self.appear(POPUP_CANCEL, interval=1):
                logger.warning(
                    "selected identical character, trying select another")
                self._cancel_popup()
                self._select_next_support()
                self.interval_reset(POPUP_CANCEL)
                continue
            if self.appear(COMBAT_SUPPORT_LIST, interval=1):
                if support_character_name != "FirstCharacter":
                    self._search_support(
                        support_character_name)  # Search support
                self.device.click(COMBAT_SUPPORT_ADD)
                self.interval_reset(COMBAT_SUPPORT_LIST)
                continue

    def _search_support(self, support_character_name: str = "JingYuan"):
        """
        Args:
            support_character_name: Support character name

        Returns:
            bool: True if found support else False

        Pages:
            in: COMBAT_SUPPORT_LIST
            out: COMBAT_SUPPORT_LIST
        """
        logger.hr("Combat support search")
        scroll = SupportListScroll(area=COMBAT_SUPPORT_LIST_SCROLL.area, color=(194, 196, 205),
                                   name=COMBAT_SUPPORT_LIST_SCROLL.name)
        if scroll.appear(main=self):
            if not scroll.at_bottom(main=self):
                # Dropdown to load the entire support list, so large threshold is acceptable
                scroll.drag_threshold, backup = 0.2, scroll.drag_threshold
                scroll.set_bottom(main=self)
                scroll.drag_threshold = backup
                scroll.set_top(main=self)

            logger.info("Searching support")
            skip_first_screenshot = False
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                if not support_character_name.startswith("Trailblazer"):
                    character = SupportCharacter(
                        support_character_name, self.device.image)
                else:
                    character = SupportCharacter(f"Stelle{support_character_name[11:]}",
                                                 self.device.image) or SupportCharacter(
                        f"Caelum{support_character_name[11:]}", self.device.image)

                if character:
                    logger.info("Support found")
                    if self._select_support(character):
                        return True
                    else:
                        logger.warning("Support not selected")
                        return False

                if not scroll.at_bottom(main=self):
                    scroll.next_page(main=self)
                    continue
                else:
                    logger.info("Support not found")
                    return False

    def _select_support(self, character: SupportCharacter):
        """
        Args:
            character: Support character

        Pages:
            in: COMBAT_SUPPORT_LIST
            out: COMBAT_SUPPORT_LIST
        """
        logger.hr("Combat support select")
        COMBAT_SUPPORT_SELECTED.matched_button.search = character.selected_icon_search()
        skip_first_screenshot = False
        interval = Timer(2)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.match_template(COMBAT_SUPPORT_SELECTED):
                return True

            if interval.reached():
                self.device.click(character)
                interval.reset()
                continue

    def _cancel_popup(self):
        """
        Pages:
            in: CANCEL_POPUP
            out: COMBAT_SUPPORT_LIST
        """
        logger.hr("Combat support cancel popup")
        skip_first_screenshot = True

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(COMBAT_SUPPORT_LIST):
                logger.info("Popup canceled")
                return

            if self.handle_popup_cancel():
                continue

    def _select_next_support(self):
        """
        Pages:
            in: COMBAT_SUPPORT_LIST
            out: COMBAT_SUPPORT_LIST
        """
        skip_first_screenshot = True
        scroll = SupportListScroll(area=COMBAT_SUPPORT_LIST_SCROLL.area, color=(194, 196, 205),
                                   name=COMBAT_SUPPORT_LIST_SCROLL.name)
        interval = Timer(1)
        next_support = None
        if scroll.appear(main=self):
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                # End
                if next_support and self._next_support_selected(next_support):
                    return

                if interval.reached():
                    next_support = NextSupportCharacter(self.device.image)
                    if next_support:
                        logger.info("Next support found, clicking")
                        self.device.click(next_support.button)
                    elif not scroll.at_bottom(main=self):
                        scroll.next_page(main=self, page=0.4)
                    else:
                        logger.warning("No more support")
                        return

                    interval.reset()
                    continue

    def _next_support_selected(self, next_support: NextSupportCharacter):
        """
        Returns:
            bool: True if selected else False
        """
        if self.match_color(next_support.button, threshold=20):
            logger.info("Next support selected")
            return True
        return False
