import re

import cv2
import numpy as np
from scipy import signal

import module.config.server as server
from module.base.timer import Timer
from module.base.utils import area_center, crop, rgb2luma
from module.config.server import VALID_LANG
from module.exception import RequestHumanTakeover, ScriptError
from module.logger import logger
from module.ocr.ocr import OcrResultButton, OcrWhiteLetterOnComplexBackground
from tasks.base.assets.assets_base_main_page import OCR_CHARACTERS, OCR_MAP_NAME, ROGUE_LEAVE_FOR_NOW
from tasks.base.assets.assets_base_page import CLOSE, MAP_EXIT
from tasks.base.page import Page, page_gacha, page_main
from tasks.base.popup import PopupHandler
from tasks.character.keywords import CharacterList
from tasks.daily.assets.assets_daily_trial import START_TRIAL
from tasks.map.keywords import KEYWORDS_MAP_PLANE, MapPlane


class OcrPlaneName(OcrWhiteLetterOnComplexBackground):
    def after_process(self, result):
        # RobotSettlement1
        result = re.sub(r'-[Ii1]$', '', result)
        result = re.sub(r'I$', '', result)
        result = re.sub(r'\d+$', '', result)
        # Herta's OfficeY/
        result = re.sub(r'Y/?$', '', result)
        # Stargazer Navatia -> Stargazer Navalia
        result = result.replace('avatia', 'avalia')
        # DomainiRespite
        result = result.replace('omaini', 'omain')
        # Domain=Combat
        result = result.replace('=', '')
        # Domain--Occunrence
        # Domain'--Occurence
        # Domain-Qccurrence
        result = result.replace('cunr', 'cur').replace('uren', 'urren').replace('Qcc', 'Occ')
        # Domain-Elit
        # Domain--Etite
        result = re.sub(r'[Ee]lit$', 'Elite', result)
        result = result.replace('tite', 'lite')

        # 区域－战
        result = re.sub(r'区域.*战$', '区域战斗', result)
        # 区域-事伴, 区域－事祥
        result = re.sub(r'事[伴祥]', '事件', result)
        # 医域－战斗
        result = result.replace('医域', '区域')
        # 区域-战半, 区域-战头, 区域-战头书
        result = re.sub(r'战[半头]', '战斗', result)
        # 区域一战斗
        result = re.sub(r'区域[\-—－一=]', '区域-', result)
        # 累塔的办公室
        result = result.replace('累塔', '黑塔')
        if '星港' in result:
            result = '迴星港'

        result = result.replace(' ', '')

        return super().after_process(result)


class OcrCharacterName(OcrWhiteLetterOnComplexBackground):
    merge_thres_x = 20
    merge_thres_y = 20

    def after_process(self, result):
        result = result.replace('蛆', '妲')

        return super().after_process(result)


class MainPage(PopupHandler):
    # Same as BigmapPlane class
    # Current plane
    plane: MapPlane = KEYWORDS_MAP_PLANE.Herta_ParlorCar
    character_buttons: list[OcrResultButton] = []
    character_current: CharacterList | None = None

    _lang_checked = False

    @property
    def characters(self) -> list[CharacterList]:
        characters = [button.matched_keyword for button in self.character_buttons]
        return characters

    def update_plane(self, lang=None) -> MapPlane | None:
        """
        Pages:
            in: page_main
        """
        if lang is None:
            lang = server.lang
        ocr = OcrPlaneName(OCR_MAP_NAME, lang=lang)
        result = ocr.ocr_single_line(self.device.image)
        # Try to match
        keyword = ocr._match_result(result, keyword_classes=MapPlane, lang=lang)
        if keyword is not None:
            self.plane = keyword
            logger.attr('CurrentPlane', keyword)
            return keyword
        # Try to remove suffix
        for suffix in range(1, 5):
            keyword = ocr._match_result(result[:-suffix], keyword_classes=MapPlane, lang=lang)
            if keyword is not None:
                self.plane = keyword
                logger.attr('CurrentPlane', keyword)
                return keyword

        return None

    def check_lang_from_map_plane(self) -> str | None:
        logger.info('check_lang_from_map_plane')
        lang_unknown = self.config.Emulator_GameLanguage == 'auto'

        if lang_unknown:
            lang_list = VALID_LANG
        else:
            # Try current lang first
            lang_list = [server.lang] + [lang for lang in VALID_LANG if lang != server.lang]

        for lang in lang_list:
            logger.info(f'Try ocr in lang {lang}')
            keyword = self.update_plane(lang)
            if keyword is not None:
                logger.info(f'check_lang_from_map_plane matched lang: {lang}')
                if lang_unknown or lang != server.lang:
                    self.config.Emulator_GameLanguage = lang
                    server.set_lang(lang)
                return lang

        if lang_unknown:
            logger.critical('Cannot detect in-game text language, please set it to 简体中文 or English')
            raise RequestHumanTakeover
        else:
            logger.warning(f'Cannot detect in-game text language, assume current lang={server.lang} is correct')
            return server.lang

    def handle_lang_check(self, page: Page):
        """
        Args:
            page:

        Returns:
            bool: If checked
        """
        if MainPage._lang_checked:
            return False
        if page != page_main:
            return False

        self.check_lang_from_map_plane()
        MainPage._lang_checked = True
        return True

    def acquire_lang_checked(self):
        """
        Returns:
            bool: If checked
        """
        if MainPage._lang_checked:
            return False

        logger.info('acquire_lang_checked')
        try:
            self.ui_goto(page_main)
        except AttributeError:
            logger.critical('Method ui_goto() not found, class MainPage must be inherited by class UI')
            raise ScriptError

        self.handle_lang_check(page=page_main)
        return True

    def update_characters(self) -> list[CharacterList]:
        ocr = OcrCharacterName(OCR_CHARACTERS)
        self.character_buttons = ocr.matched_ocr(self.device.image, keyword_classes=CharacterList)
        characters = self.characters
        logger.attr('Characters', characters)
        self.character_current = self._convert_selected_to_character(self._update_current_character())
        return characters

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
        expected_peaks = np.array([201, 279, 357, 435])
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
        Args:
            character: CharacterList object, or character name, or select index from 1 to 4.
            skip_first_screenshot:

        Returns:
            bool: If chose
        """
        logger.info(f'Character choose: {character}')
        characters = self.characters
        if isinstance(character, int):
            character = self._convert_selected_to_character([character])
            if character is None:
                return False
            try:
                index = characters.index(character) + 1
            except IndexError:
                logger.warning(f'Cannot choose character {character} as it was not detected')
                return False
        else:
            if isinstance(character, str):
                character = CharacterList.find(character)
            try:
                index = characters.index(character) + 1
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

            try:
                is_in_main = self.is_in_main
            except AttributeError:
                logger.critical('Method ui_goto() not found, class MainPage must be inherited by class UI')
                raise ScriptError

            if interval.reached() and is_in_main():
                self.device.click(button)
                interval.reset()
                count += 1

    def ui_leave_special(self):
        """
        Leave from:
        - Rogue domains
        - Character trials

        Returns:
            bool: If left a special plane

        Pages:
            in: Any
            out: page_main
        """
        if not self.appear(MAP_EXIT):
            return False

        logger.info('UI leave special')
        skip_first_screenshot = True
        clicked = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if clicked:
                if self.appear(page_main.check_button):
                    logger.info(f'Leave to {page_main}')
                    break

            if self.appear_then_click(MAP_EXIT, interval=2):
                continue
            if self.handle_popup_confirm():
                continue
            if self.match_template_color(START_TRIAL, interval=2):
                logger.info(f'{START_TRIAL} -> {CLOSE}')
                self.device.click(CLOSE)
                clicked = True
                continue
            if self.handle_ui_close(page_gacha.check_button, interval=2):
                continue
            if self.appear_then_click(ROGUE_LEAVE_FOR_NOW, interval=2):
                clicked = True
                continue
