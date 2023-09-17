import re
from typing import Optional

import module.config.server as server
from module.base.base import ModuleBase
from module.config.server import VALID_LANG
from module.exception import RequestHumanTakeover, ScriptError
from module.logger import logger
from module.ocr.ocr import Ocr
from tasks.base.assets.assets_base_main_page import OCR_MAP_NAME
from tasks.base.page import Page, page_main
from tasks.map.keywords import KEYWORDS_MAP_PLANE, MapPlane


class OcrPlaneName(Ocr):
    def after_process(self, result):
        # RobotSettlement1
        result = re.sub(r'-[Ii1]$', '', result)
        result = re.sub(r'\d+$', '', result)

        return super().after_process(result)


class MainPage(ModuleBase):
    # Same as BigmapPlane class
    # Current plane
    plane: MapPlane = KEYWORDS_MAP_PLANE.Herta_ParlorCar

    _lang_checked = False

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
            ocr = OcrPlaneName(OCR_MAP_NAME, lang=lang)
            result = ocr.ocr_single_line(self.device.image)
            keyword = ocr._match_result(result, keyword_classes=MapPlane, lang=lang)
            if keyword is not None:
                self.plane = keyword
                logger.attr('CurrentPlane', self.plane)
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
