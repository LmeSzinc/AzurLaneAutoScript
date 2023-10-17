import cv2
import numpy as np
from pponnxcr.predict_system import BoxedResult

from module.base.base import ModuleBase
from module.base.timer import Timer
from module.base.utils import area_offset, color_similarity_2d, crop
from module.logger.logger import logger
from module.ocr.keyword import Keyword
from module.ocr.ocr import Ocr, OcrResultButton
from module.ui.draggable_list import DraggableList
from tasks.base.assets.assets_base_page import FORGOTTEN_HALL_CHECK, MAP_EXIT
from tasks.dungeon.keywords import DungeonList, KEYWORDS_DUNGEON_LIST, KEYWORDS_DUNGEON_TAB
from tasks.dungeon.ui import DungeonUI
from tasks.forgotten_hall.assets.assets_forgotten_hall_ui import *
from tasks.forgotten_hall.keywords import ForgottenHallStage, KEYWORDS_FORGOTTEN_HALL_STAGE
from tasks.forgotten_hall.team import ForgottenHallTeam
from tasks.map.control.joystick import MapControlJoystick


class ForgottenHallStageOcr(Ocr):
    def _find_number(self, image):
        raw = image.copy()
        area = OCR_STAGE.area
        image = crop(raw, area)
        yellow = color_similarity_2d(image, color=(255, 200, 112))
        gray = color_similarity_2d(image, color=(100, 109, 134))
        image = np.maximum(yellow, gray)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)

        _, image = cv2.threshold(image, 220, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        rectangle = []
        for cont in contours:
            rect = cv2.boundingRect(cv2.convexHull(cont).astype(np.float32))
            # Filter with rectangle width, usually to be 62~64
            if not 62 - 10 < rect[2] < 65 + 10:
                continue
            rect = (rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3])
            rect = area_offset(rect, offset=area[:2])
            # Move from stars to letters
            rect = area_offset((-10, -55, 50, -15), offset=rect[:2])
            rectangle.append(rect)
        return rectangle

    def matched_ocr(self, image, keyword_classes, direct_ocr=False) -> list[OcrResultButton]:
        if not isinstance(keyword_classes, list):
            keyword_classes = [keyword_classes]

        boxes = self._find_number(image)
        image_list = [crop(image, area) for area in boxes]
        results = self.ocr_multi_lines(image_list)
        results = [
            BoxedResult(area_offset(boxes[index], (-50, 0)), image_list[index], text, score)
            for index, (text, score) in enumerate(results)
        ]

        results = [self._product_button(result, keyword_classes, ignore_digit=False) for result in results]
        results = [result for result in results if result.is_keyword_matched]

        logger.attr(name=f'{self.name} matched', text=results)
        return results


class DraggableStageList(DraggableList):
    def insight_row(self, row: Keyword, main: ModuleBase, skip_first_screenshot=True) -> bool:
        while 1:
            result = super().insight_row(row, main=main, skip_first_screenshot=skip_first_screenshot)
            if not result:
                if row == KEYWORDS_FORGOTTEN_HALL_STAGE.Stage_1:
                    # Must have stage 1, retry if not found
                    continue
                else:
                    return False

            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()
            button = self.keyword2button(row)

            # end
            if button.button[0] > 0:
                break

            # Stage number is insight but button is not
            logger.info("Stage number is insight, swipe left a little bit to find the entrance")
            self.drag_vector = (0.2, 0.4)
            self.drag_page("left", main=main)
            self.drag_vector = DraggableList.drag_vector
        return True

    def is_row_selected(self, button: OcrResultButton, main: ModuleBase) -> bool:
        return main.appear(ENTRANCE_CHECKED)

    def load_rows(self, main: ModuleBase):
        if not main.appear(FORGOTTEN_HALL_CHECK):
            logger.info('Not in forgotten hall, skip load_rows()')
            return
        return super().load_rows(main=main)


STAGE_LIST = DraggableStageList("ForgottenHallStageList", keyword_class=ForgottenHallStage,
                                ocr_class=ForgottenHallStageOcr, search_button=OCR_STAGE,
                                check_row_order=False, drag_direction="right")


class ForgottenHallUI(DungeonUI, ForgottenHallTeam):
    def handle_effect_popup(self):
        if self.appear(EFFECT_NOTIFICATION, interval=2):
            if self.appear_then_click(MEMORY_OF_CHAOS_CHECK):
                return True
            if self.appear_then_click(MEMORY_OF_CHAOS_CLICK):
                return True
            # No match, click whatever
            MEMORY_OF_CHAOS_CHECK.clear_offset()
            self.device.click(MEMORY_OF_CHAOS_CHECK)
            return True

        return False

    def stage_choose(self, dungeon: DungeonList, skip_first_screenshot=True):
        """
        Pages:
            in: page_forgotten_hall, FORGOTTEN_HALL_CHECK
                or page_guide, Survival_Index, Forgotten_Hall
            out: page_forgotten_hall, FORGOTTEN_HALL_CHECK, selected at the given dungeon tab
        """
        logger.info(f'Stage choose {dungeon}')
        if dungeon == KEYWORDS_DUNGEON_LIST.Memory_of_Chaos:
            check_button = MEMORY_OF_CHAOS_CHECK
            click_button = MEMORY_OF_CHAOS_CLICK
        elif dungeon == KEYWORDS_DUNGEON_LIST.The_Last_Vestiges_of_Towering_Citadel:
            check_button = LAST_VASTIGES_CHECK
            click_button = LAST_VASTIGES_CLICK
        else:
            logger.error(f'Choosing {dungeon} in forgotten hall is not supported')
            return

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # interval used in end condition
            # After clicking `click_button`, `click_button` appears, then screen goes black for a little while
            # interval prevents `check_button` being triggered in the next 0.3s
            if self.match_template_color(check_button, interval=0.3):
                logger.info(f'Stage chose at {dungeon}')
                break
            if self.handle_effect_popup():
                continue
            if self.appear_then_click(TELEPORT, interval=2):
                continue
            if self.match_template_color(click_button, interval=1):
                self.device.click(click_button)
                self.interval_reset(check_button)
                continue

    def stage_goto(self, dungeon: DungeonList, stage_keyword: ForgottenHallStage):
        """
        Examples:
            self = ForgottenHallUI('alas')
            self.device.screenshot()
            self.stage_goto(KEYWORDS_DUNGEON_LIST.The_Last_Vestiges_of_Towering_Citadel,
                            KEYWORDS_FORGOTTEN_HALL_STAGE.Stage_8)
        """
        if not dungeon in [
            KEYWORDS_DUNGEON_LIST.Memory_of_Chaos,
            KEYWORDS_DUNGEON_LIST.The_Last_Vestiges_of_Towering_Citadel,

        ]:
            logger.error(f'DungeonList Chosen is not a forgotten hall: {dungeon}')
            return
        if dungeon == KEYWORDS_DUNGEON_LIST.Memory_of_Chaos and stage_keyword.id > 10:
            logger.error(f'This dungeon "{dungeon}" does not have stage that greater than 10. '
                         f'{stage_keyword.id} is chosen')
            return

        if self.appear(FORGOTTEN_HALL_CHECK):
            logger.info('Already in forgotten hall')
        else:
            self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
            self._dungeon_nav_goto(dungeon)

        self.stage_choose(dungeon)
        STAGE_LIST.select_row(stage_keyword, main=self)

    def exit_dungeon(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_main, in forgotten hall map
            out: page_forgotten_hall, FORGOTTEN_HALL_CHECK
        """
        logger.info('Exit dungeon')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(FORGOTTEN_HALL_CHECK):
                logger.info("Forgotten hall dungeon exited")
                break

            if self.appear_then_click(MAP_EXIT):
                continue
            if self.handle_popup_confirm():
                continue
            if self.handle_popup_single():
                continue

    def enter_forgotten_hall_dungeon(self, skip_first_screenshot=True):
        """
        called after team is set

        Pages:
            in: ENTRANCE_CHECKED, ENTER_FORGOTTEN_HALL_DUNGEON
            out: page_main, in forgotten hall map
        """
        interval = Timer(3)
        timeout = Timer(3)
        while 1:  # enter ui -> popup
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(EFFECT_NOTIFICATION):
                break
            if self.match_template_color(DUNGEON_ENTER_CHECKED):
                if timeout.reached():
                    logger.info('Wait dungeon EFFECT_NOTIFICATION timeout')
                    break
            else:
                timeout.reset()

            if interval.reached() and self.team_prepared():
                self.device.click(ENTER_FORGOTTEN_HALL_DUNGEON)
                interval.reset()

        joystick = MapControlJoystick(self.config, self.device)
        skip_first_screenshot = True
        while 1:  # pop up -> dungeon inside
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.match_template_color(DUNGEON_ENTER_CHECKED):
                logger.info("Forgotten hall dungeon entered")
                break
            joystick.handle_map_run_2x()
