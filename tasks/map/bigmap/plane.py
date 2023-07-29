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
    # Floor name in game (B1, F1, F2, ...)
    floor: str = 'F1'

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

        if SCROLL_PLANE.appear(main=self):
            if plane.page == 'top':
                if SCROLL_PLANE.set_top(main=self):
                    PLANE_LIST.load_rows(main=self)
            elif plane.page == 'bottom':
                if SCROLL_PLANE.set_bottom(main=self):
                    PLANE_LIST.load_rows(main=self)

        PLANE_LIST.select_row(plane, main=self, insight=False)
        self.plane = plane
        return True

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
                return index + 1

        # logger.warning('Cannot get current floor')
        return 0

    def _bigmap_floor_set_execute(self, index: int, skip_first_screenshot=True) -> bool:
        """
        Args:
            index: 1 to 3, note that floor always starts from 1 (1, 2, 3, ...),
                different from the floor name in game (B1, F1, F2).

        Returns:
            bool: If success.

        Pages:
            in: page_map
        """
        logger.info(f'Bigmap floor index set: {index}')
        try:
            button = FLOOR_BUTTONS[index - 1]
        except IndexError:
            logger.error(f'No floor button matches floor index: {index}')
            return False

        interval = Timer(2)
        click_count = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            current = self._bigmap_get_current_floor()
            logger.attr('FloorIndex', current)

            # End
            if current == index:
                logger.info('Selected at target floor index')
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

    def bigmap_floor_set(self, floor: int | str, skip_first_screenshot=True) -> bool:
        """
        bigmap_plane_set() or _bigmap_get_current_plane_wrapped() must be called first
        which means `self.plane` is set.

        Args:
            floor: int for floor index counted from bottom, started from 1, such as 1, 2, 3.
                str for flooe name in game, such as "B1", "F1", "F2".
            skip_first_screenshot:

        Returns:
            bool: If success.

        Raises:
            ScriptError: If the given floor doesn't exist on current plane.

        Pages:
            in: page_map

        Examples:
            self = BigmapPlane('alas')
            self.bigmap_plane_set(KEYWORDS_MAP_PLANE.Jarilo_RivetTown)
            self.bigmap_floor_set('F2')
        """
        if isinstance(floor, int):
            self.plane.convert_to_floor_name(floor)
            index = floor
        else:
            floor = str(floor)
            index = self.plane.convert_to_floor_index(floor)

        return self._bigmap_floor_set_execute(index, skip_first_screenshot=skip_first_screenshot)
