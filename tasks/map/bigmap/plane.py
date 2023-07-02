import re
from typing import Optional

from module.base.base import ModuleBase
from module.exception import ScriptError
from module.logger import logger
from module.ocr.ocr import Ocr, OcrResultButton
from module.ui.draggable_list import DraggableList
from module.ui.scroll import Scroll
from tasks.base.page import page_map, page_world
from tasks.base.ui import UI
from tasks.map.assets.assets_map_bigmap import *
from tasks.map.keywords import MapPlane, KEYWORDS_MAP_PLANE
from module.base.timer import Timer


def world_entrance(plane: MapPlane) -> ButtonWrapper:
    if plane.is_HertaSpaceStation:
        return WORLD_HERTA
    if plane.is_JariloVI:
        return WORLD_JARILO
    if plane.is_Luofu:
        return WORLD_LUOFU
    raise ScriptError(f'world_entrance() got unknown plane: {plane}')


class OcrMapPlane(Ocr):
    merge_thres_y = 20

    def after_process(self, result):
        result = super().after_process(result)
        result = re.sub(r'[+→★“”,.，、。]', '', result).strip()
        if self.lang == 'ch':
            result = result.replace('迎星港', '迴星港')
        return result


class DraggablePlaneList(DraggableList):
    def is_row_selected(self, button: OcrResultButton, main: ModuleBase) -> bool:
        # Items have an animation to be selected, check if the rightmost become black.
        x = OCR_PLANE.area[2]
        area = (x - 20, button.area[1], x, button.area[3])
        if main.image_color_count(area, color=(40, 40, 40), threshold=221, count=100):
            return True

        return False


SCROLL_PLANE = Scroll(PLANE_SCROLL, color=(67, 67, 67), name='SCROLL_PLANE')
PLANE_LIST = DraggablePlaneList('PlaneList', keyword_class=MapPlane, ocr_class=OcrMapPlane, search_button=OCR_PLANE)


class BigmapPlane(UI):
    def _bigmap_world_set(self, plane: MapPlane):
        """
        Pages:
            in: Any
            out: page_map
        """
        self.ui_goto(page_world)
        self.ui_click(appear_button=page_world.check_button,
                      click_button=world_entrance(plane),
                      check_button=page_map.check_button)

    def _bigmap_get_current_plane(self) -> Optional[MapPlane]:
        """
        Get current plane.
        After entering page_map, the current plane is selected by default.

        Pages:
            in: page_map
        """
        PLANE_LIST.load_rows(main=self)
        selected = PLANE_LIST.get_selected_row(main=self)
        if selected is None:
            return None
        else:
            return selected.matched_keyword

    def _bigmap_get_current_plane_wrapped(self) -> MapPlane:
        """
        Get current plane with reties.
        """
        for n in range(2):
            self.ui_ensure(page_map)

            # Wait select animation
            timeout = Timer(2).start()
            skip_first_screenshot = True
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()
                current = self._bigmap_get_current_plane()
                if current is not None:
                    return current
                if timeout.reached():
                    logger.warning('No plane was selected')
                    if n == 0:
                        # Nothing selected, probably because it has been switched to page_map before running.
                        # Exit and re-enter should fix it.
                        self.ui_goto_main()
                    break

        logger.error('Cannot find current plane, return the first plane in list instead')
        try:
            first = PLANE_LIST.cur_buttons[0].matched_keyword
            if first is not None:
                return first
            else:
                return KEYWORDS_MAP_PLANE.Herta_ParlorCar
        except IndexError:
            return KEYWORDS_MAP_PLANE.Herta_ParlorCar

    def bigmap_plane_set(self, plane: MapPlane):
        """
        Set map ti given plane.

        Args:
            plane:

        Returns:
            bool: If success.

        Pages:
            in: Any
            out: page_map
        """
        logger.info(f'Bigmap plane set: {plane}')
        current = self._bigmap_get_current_plane_wrapped()
        logger.attr('CurrentPlane', current)

        if current.world != plane.world:
            logger.info(f'Switch to world {plane.world}')
            self._bigmap_world_set(plane)
            PLANE_LIST.load_rows(main=self)

        if plane.is_HertaSpaceStation:
            PLANE_LIST.select_row(plane, main=self, insight=False)
            return True
        elif plane.is_JariloVI:
            if plane in [
                KEYWORDS_MAP_PLANE.Jarilo_AdministrativeDistrict,
                KEYWORDS_MAP_PLANE.Jarilo_OutlyingSnowPlains,
                KEYWORDS_MAP_PLANE.Jarilo_BackwaterPass,
                KEYWORDS_MAP_PLANE.Jarilo_SilvermaneGuardRestrictedZone,
                KEYWORDS_MAP_PLANE.Jarilo_CorridorofFadingEchoes,
                KEYWORDS_MAP_PLANE.Jarilo_EverwinterHill,
            ]:
                if SCROLL_PLANE.set_top(main=self):
                    PLANE_LIST.load_rows(main=self)
            else:
                if SCROLL_PLANE.set_bottom(main=self):
                    PLANE_LIST.load_rows(main=self)

            PLANE_LIST.select_row(plane, main=self, insight=False)
            return True
        elif plane.is_Luofu:
            PLANE_LIST.select_row(plane, main=self, insight=False)
            return True

        logger.error(f'Goto plane {plane} is not supported')
        return False
