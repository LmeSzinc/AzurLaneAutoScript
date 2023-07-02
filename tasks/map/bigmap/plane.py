import re
from typing import Optional

from module.base.base import ModuleBase
from module.base.timer import Timer
from module.exception import ScriptError
from module.logger import logger
from module.ocr.ocr import Ocr, OcrResultButton
from module.ui.draggable_list import DraggableList
from module.ui.scroll import Scroll
from tasks.base.page import page_map, page_world
from tasks.base.ui import UI
from tasks.map.assets.assets_map_bigmap import *
from tasks.map.keywords import KEYWORDS_MAP_PLANE, MapPlane

FLOOR_BUTTONS = [FLOOR_1, FLOOR_2, FLOOR_3]


def world_entrance(plane: MapPlane) -> ButtonWrapper:
    if plane.is_HertaSpaceStation:
        return WORLD_HERTA
    if plane.is_JariloVI:
        return WORLD_JARILO
    if plane.is_Luofu:
        return WORLD_LUOFU
    raise ScriptError(f'world_entrance() got unknown plane: {plane}')


def convert_ingame_floor(plane: MapPlane, floor: int | str) -> int:
    """
    Convert floor name in game to the name in SRC.

    Args:
        plane:
        floor: Floor name in game, such as -1, 1, 2, "B1", "F1", "F2"

    Returns:
        int: 1 to 3 counted from bottom.

    Raises:
        KeyError: If failed to convert.
    """
    if isinstance(floor, str):
        try:
            floor = int(floor)
        except ValueError:
            dic_floor = {
                'B2': -2,
                'B1': -1,
                'F1': 1,
                'F2': 2,
                'F3': 3,
                'F4': 4,
                'F5': 5,
            }
            floor = dic_floor[floor.upper()]

    dic_floor = {}
    if plane == KEYWORDS_MAP_PLANE.Herta_StorageZone:
        dic_floor = {-1: 1, 1: 2, 2: 3}
    if plane == KEYWORDS_MAP_PLANE.Herta_SupplyZone:
        dic_floor = {1: 1, 2: 2}
    if plane == KEYWORDS_MAP_PLANE.Jarilo_AdministrativeDistrict:
        dic_floor = {-1: 1, 1: 2}
    if plane in [KEYWORDS_MAP_PLANE.Jarilo_RivetTown,
                 KEYWORDS_MAP_PLANE.Jarilo_RobotSettlement]:
        dic_floor = {1: 1, 2: 2}
    if plane in [KEYWORDS_MAP_PLANE.Luofu_Cloudford,
                 KEYWORDS_MAP_PLANE.Luofu_StargazerNavalia,
                 KEYWORDS_MAP_PLANE.Luofu_DivinationCommission]:
        dic_floor = {1: 1, 2: 2}

    floor = dic_floor[floor]
    return floor


class OcrMapPlane(Ocr):
    merge_thres_y = 20

    def after_process(self, result):
        result = super().after_process(result)
        result = re.sub(r'[+→★“”,.，、。]', '', result).strip()
        if self.lang == 'ch':
            result = result.replace('迎星港', '迴星港')
            if result == '星港':
                result = '迴星港'
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
    # Current plane
    plane: MapPlane = KEYWORDS_MAP_PLANE.Herta_ParlorCar
    # Current floor
    # Note that floor always starts from 1 (1, 2, 3, ...)
    # which is different from the floor in game (B1, F1, F2, ...)
    floor: int = 1

    def _bigmap_world_set(self, plane: MapPlane):
        """
        Pages:
            in: Any
            out: page_map
        """
        self.ui_goto(page_world)
        self.ui_click(appear_button=page_world.check_button,
                      click_button=world_entrance(plane),
                      check_button=page_map.check_button,
                      retry_wait=1)

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
                    self.plane = current
                    return self.plane
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
                self.plane = first
                return self.plane
            else:
                self.plane = KEYWORDS_MAP_PLANE.Herta_ParlorCar
                return self.plane
        except IndexError:
            self.plane = KEYWORDS_MAP_PLANE.Herta_ParlorCar
            return self.plane

    def bigmap_plane_set(self, plane: MapPlane) -> bool:
        """
        Set map to the given plane.

        Args:
            plane:

        Returns:
            bool: If success.

        Pages:
            in: Any
            out: page_map
        """
        logger.info(f'Bigmap plane set: {plane}')
        self._bigmap_get_current_plane_wrapped()
        logger.attr('CurrentPlane', self.plane)

        if self.plane.world != plane.world:
            logger.info(f'Switch to world {plane.world}')
            self._bigmap_world_set(plane)
            PLANE_LIST.load_rows(main=self)

        if plane.is_HertaSpaceStation:
            PLANE_LIST.select_row(plane, main=self, insight=False)
            self.plane = plane
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
            self.plane = plane
            return True
        elif plane.is_Luofu:
            PLANE_LIST.select_row(plane, main=self, insight=False)
            self.plane = plane
            return True

        logger.error(f'Goto plane {plane} is not supported')
        return False

    def _bigmap_get_current_floor(self) -> int:
        """
        Pages:
            in: page_map
        """
        for index, button in enumerate(FLOOR_BUTTONS):
            # Gray button, not current floor
            if self.image_color_count(button, color=(117, 117, 117), threshold=221, count=200):
                continue
            # White button, current floor
            if self.image_color_count(button, color=(233, 233, 233), threshold=221, count=200):
                self.floor = index + 1
                return self.floor

        # logger.warning('Cannot get current floor')
        self.floor = 0
        return self.floor

    def _bigmap_floor_set_execute(self, floor: int, skip_first_screenshot=True) -> bool:
        """
        Args:
            floor: 1 to 3

        Returns:
            bool: If success.

        Pages:
            in: page_map
        """
        logger.info(f'Bigmap floor set: {floor}')
        try:
            button = FLOOR_BUTTONS[floor - 1]
        except IndexError:
            logger.error(f'No floor button matches floor index: {floor}')
            return False

        interval = Timer(2)
        click_count = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            self._bigmap_get_current_floor()
            logger.attr('CurrentFloor', self.floor)

            # End
            if self.floor == floor:
                logger.info('Selected at target row')
                return True
            if click_count >= 3:
                logger.warning('Unable to set floor after 3 trial, assume floor set')
                return False

            # Click
            if interval.reached():
                self.device.click(button)
                interval.reset()
                click_count += 1
                continue

    def bigmap_floor_set(self, floor: int = 0, ingame_floor: int | str = 0, skip_first_screenshot=True) -> bool:
        """
        bigmap_plane_set() or _bigmap_get_current_plane_wrapped() must be called first.

        Args:
            floor: 1 to 3 counted from bottom.
                If `floor` given, use it first. One of `floor` and `ingame_floor`
            ingame_floor: Floor name in game, such as -1, 1, 2, "B1", "F1", "F2"
            skip_first_screenshot:

        Returns:
            bool: If success.

        Pages:
            in: page_map
        """
        if not floor:
            if ingame_floor:
                try:
                    floor = convert_ingame_floor(plane=self.plane, floor=ingame_floor)
                except KeyError:
                    logger.error(f'Plane {self.plane} does not have floor {ingame_floor}')
                    return False
            else:
                logger.error('bigmap_floor_set() did not receive any floor inputs')
                return False

        return self._bigmap_floor_set_execute(floor, skip_first_screenshot=skip_first_screenshot)
