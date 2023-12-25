import re

import cv2
import numpy as np
from scipy import signal

from module.base.timer import Timer
from module.base.utils import area_center, crop, rgb2luma
from module.logger import logger
from module.ocr.ocr import BoxedResult, OcrResultButton, OcrWhiteLetterOnComplexBackground
from tasks.base.ui import UI
from tasks.character.assets.assets_character_switch import *
from tasks.character.keywords import CharacterList, DICT_SORTED_RANGES, KEYWORD_CHARACTER_LIST


class OcrCharacterName(OcrWhiteLetterOnComplexBackground):
    merge_thres_x = 20
    merge_thres_y = 20

    def after_process(self, result):
        result = result.replace('蛆', '妲')
        # Dan Heng o.ImbibitorLunae
        result = re.sub(r'[0Oo\-. ]{1,3}Imbi', 'Imbi', result)

        return super().after_process(result)


class CharacterSwitch(UI):
    characters: list[CharacterList] = []
    character_current: CharacterList | None = None
    character_buttons: list[OcrResultButton] = []

    def character_update(self, skip_first_screenshot=True) -> list[CharacterList]:
        """
        The following properties will be updated:
        - self.characters
        - self.character_current
        - self.character_buttons

        Pages:
            in: page_main
        """
        timeout = Timer(1, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if timeout.reached():
                logger.warning('Character update timeout')
                break

            ocr = OcrCharacterName(OCR_MAP_CHARACTERS)
            buttons = ocr.matched_ocr(self.device.image, keyword_classes=CharacterList)
            if trailblazer := self._get_character_trailblazer():
                buttons.append(trailblazer)
            buttons = sorted(buttons, key=lambda b: area_center(b.area)[1])
            self.character_buttons = buttons

            self.characters = [button.matched_keyword for button in self.character_buttons]
            logger.attr('Characters', self.characters)
            self.character_current = self._convert_selected_to_character(self._update_current_character())

            # Must contain first character
            if not buttons:
                continue
            expected_peaks = np.array([201, 279, 357, 435])
            if buttons[0].area[3] < expected_peaks[0]:
                break
            else:
                logger.info('No first character, retrying')
                continue

        return self.characters

    def _get_character_trailblazer(self) -> OcrResultButton | None:
        dict_template = {
            KEYWORD_CHARACTER_LIST.TrailblazerDestruction: [
                TrailblazerDestructionMale,
                TrailblazerDestructionFemale,
            ],
            KEYWORD_CHARACTER_LIST.TrailblazerPreservation: [
                TrailblazerPreservationMale,
                TrailblazerPreservationFemale,

            ],
        }
        for character, templates in dict_template.items():
            for template in templates:
                template.load_search(TRAILBLAZER_SEARCH.area)
                if template.match_template(self.device.image):
                    logger.info(f'Found trailblazer: {template}')
                    # Create a fake OcrResultButton object
                    box = BoxedResult(box=template.button, text_img=None, ocr_text='', score=1.0)
                    button = OcrResultButton(boxed_result=box, matched_keyword=character)
                    return button
        return None

    def _update_current_character(self) -> list[int]:
        """
        Returns:
            list[int]: Selected index, 1 to 4.
        """
        # 50px-width area starting from the right edge of HP bars
        area = (1101, 151, 1151, 459)
        # Y coordinates where the color peaks should be when character is selected
        expected_peaks = np.array([201, 279, 357, 435])
        expected_peaks_in_area = expected_peaks - area[1]
        # Use Luminance to fit H264 video stream
        image = rgb2luma(crop(self.device.image, area))
        # Remove character names
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        image = cv2.erode(image, kernel)
        # To find peaks along Y
        line = cv2.reduce(image, 1, cv2.REDUCE_AVG).flatten().astype(int)

        # Find color peaks
        parameters = {
            'height': (60, 255),
            'prominence': 30,
            'distance': 5,
        }
        peaks, _ = signal.find_peaks(line, **parameters)
        # Remove smooth peaks
        parameters = {
            'height': (5, 255),
            'prominence': 5,
            'distance': 5,
        }
        diff = -np.diff(line)
        diff_peaks, _ = signal.find_peaks(diff, **parameters)

        def is_steep_peak(y, threshold=5):
            return np.abs(diff_peaks - y).min() <= threshold

        def peak_to_selected(y, threshold=5):
            distance = np.abs(expected_peaks_in_area - y)
            return np.argmin(distance) + 1 if distance.min() < threshold else 0

        selected = [peak_to_selected(peak) for peak in peaks if peak_to_selected(peak) and is_steep_peak(peak)]
        logger.attr('CharacterSelected', selected)
        return selected

    def _convert_selected_to_character(self, selected: list[int]) -> CharacterList | None:
        expected_peaks = [201, 279, 357, 435]
        if not selected:
            logger.warning(f'No current character')
            logger.attr('CurrentCharacter', None)
            return None
        elif len(selected) == 1:
            selected = selected[0]
        else:
            logger.warning(f'Too many current characters: {selected}, using first')
            selected = selected[0]

        expected_y = expected_peaks[selected - 1]
        for button in self.character_buttons:
            y = area_center(button.area)[1]
            if expected_y - 78 < y < expected_y:
                logger.attr('CurrentCharacter', button.matched_keyword)
                return button.matched_keyword

        logger.warning(f'Current character: {selected} does not belong to any detected character')
        logger.attr('CurrentCharacter', None)
        return None

    def character_switch(self, character: CharacterList | str | int, skip_first_screenshot=True) -> bool:
        """
        character_update() must be called before switching.

        Args:
            character: CharacterList object, or character name, or select index from 1 to 4.
            skip_first_screenshot:

        Returns:
            bool: If chose
        """
        logger.info(f'Character choose: {character}')
        if isinstance(character, int):
            character = self._convert_selected_to_character([character])
            if character is None:
                return False
            try:
                index = self.characters.index(character) + 1
            except IndexError:
                logger.warning(f'Cannot choose character {character} as it was not detected')
                return False
        else:
            if isinstance(character, str):
                character = CharacterList.find(character)
            try:
                index = self.characters.index(character) + 1
            except IndexError:
                logger.warning(f'Cannot choose character {character} as it was not detected')
                return False

        button = self.character_buttons[index - 1]
        interval = Timer(1, count=3)
        count = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            selected = self._update_current_character()
            if index in selected:
                logger.info('Character chose')
                return True
            if count > 3:
                logger.warning('Failed to choose character, assume chose')
                return False

            if interval.reached() and self.is_in_main():
                self.device.click(button)
                interval.reset()
                count += 1

    def _get_ranged_character(self) -> CharacterList | bool:
        # Check if it's using a ranged character already
        for level, character_list in DICT_SORTED_RANGES.items():
            if self.character_current in character_list:
                logger.info(f'Already using a ranged character: {self.character_current}, range={level}')
                return True
        # Check if there is a ranged character in team
        for level, character_list in DICT_SORTED_RANGES.items():
            for ranged_character in character_list:
                if ranged_character in self.characters:
                    logger.info(f'Use ranged character: {ranged_character}, range={level}')
                    return ranged_character
        # No kids, as low camera height may miss enemy aim icon
        if self.character_current.height == 'Kid':
            # Switch to whoever tall
            for height in ['Male', 'Lad', 'Lady', 'Miss', 'Maid', 'Boy', 'Girl']:
                for tall_character in self.characters:
                    if tall_character.height == height:
                        logger.info(f'No kids, use tall character: {tall_character}')
                        return tall_character
        # No ranged characters
        logger.info('No ranged characters in team')
        return False

    def character_switch_to_ranged(self, update=True) -> bool:
        """
        Args:
            update: If update characters before switching

        Returns:
            bool: If using a ranged character now
        """
        logger.hr('Character switch to ranged')
        if update:
            self.character_update()

        character = self._get_ranged_character()
        if character is True:
            return True
        elif character is False:
            return False
        else:
            return self.character_switch(character)
