import re
from typing import Optional

import module.config.server as server
from module.config.server import VALID_LANG
from module.exception import RequestHumanTakeover, ScriptError
from module.logger import logger
from module.ocr.ocr import Ocr
from tasks.base.assets.assets_base_main_page import OCR_MAP_NAME, ROGUE_LEAVE_FOR_NOW
from tasks.base.assets.assets_base_page import CLOSE, MAP_EXIT
from tasks.base.page import Page, page_gacha, page_main
from tasks.base.popup import PopupHandler
from tasks.daily.assets.assets_daily_trial import START_TRIAL
from tasks.map.keywords import KEYWORDS_MAP_PLANE, MapPlane


class OcrPlaneName(Ocr):
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


class MainPage(PopupHandler):
    # Same as BigmapPlane class
    # Current plane
    plane: MapPlane = KEYWORDS_MAP_PLANE.Herta_ParlorCar

    _lang_checked = False

    def get_plane(self, lang=None) -> Optional[MapPlane]:
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

    def check_lang_from_map_plane(self) -> Optional[str]:
        logger.info('check_lang_from_map_plane')
        lang_unknown = self.config.Emulator_GameLanguage == 'auto'

        if lang_unknown:
            lang_list = VALID_LANG
        else:
            # Try current lang first
            lang_list = [server.lang] + [lang for lang in VALID_LANG if lang != server.lang]

        for lang in lang_list:
            logger.info(f'Try ocr in lang {lang}')
            keyword = self.get_plane(lang)
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
