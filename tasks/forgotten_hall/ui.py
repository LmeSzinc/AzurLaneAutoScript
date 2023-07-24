import cv2
import numpy as np
from ppocronnx.predict_system import BoxedResult

from module.base.base import ModuleBase
from module.base.timer import Timer
from module.base.utils import area_offset, color_similarity_2d, crop, get_color
from module.logger.logger import logger
from module.ocr.keyword import Keyword
from module.ocr.ocr import Ocr, OcrResultButton
from module.ui.draggable_list import DraggableList
from tasks.base.assets.assets_base_page import FORGOTTEN_HALL_CHECK
from tasks.dungeon.keywords import DungeonList, KEYWORDS_DUNGEON_TAB
from tasks.dungeon.ui import DungeonUI
from tasks.forgotten_hall.assets.assets_forgotten_hall import *
from tasks.forgotten_hall.keywords import *
from tasks.map.control.joystick import MapControlJoystick


class ForgottenHallStageOcr(Ocr):
    def _find_number(self, image):
        raw = image.copy()
        area = OCR_STAGE.area
        image = crop(raw, area)
        yellow = color_similarity_2d(image, color=(250, 201, 111))
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
            if not 62 - 10 < rect[2] < 62 + 10:
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
        boxed_results = [
            BoxedResult(area_offset(boxes[index], (-50, 0)), image_list[index], text, score)
            for index, (text, score) in enumerate(results)
        ]
        results_buttons = [
            OcrResultButton(result, keyword_classes)
            for result in boxed_results
        ]
        logger.attr(name=f'{self.name} matched', text=results_buttons)
        return results_buttons


class DraggableStageList(DraggableList):
    def insight_row(self, row: Keyword, main: ModuleBase, skip_first_screenshot=True) -> bool:
        while 1:
            result = super().insight_row(row, main=main, skip_first_screenshot=skip_first_screenshot)
            if not result:
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


class ForgottenHallUI(DungeonUI):
    def stage_goto(self, forgotten_hall: DungeonList, stage_keyword: ForgottenHallStage):
        """
        Examples:
            self = ForgottenHallUI('alas')
            self.device.screenshot()
            self.stage_goto(KEYWORDS_DUNGEON_LIST.The_Last_Vestiges_of_Towering_Citadel,
                            KEYWORDS_FORGOTTEN_HALL_STAGE.Stage_8)
        """
        if not forgotten_hall.is_Forgotten_Hall:
            logger.warning("DungeonList Chosen is not a forgotten hall")
            return
        if not forgotten_hall.is_Last_Vestiges and stage_keyword.id > 10:
            logger.warning(f"This dungeon does not have stage that greater than 10. {stage_keyword.id} is chosen")
            return

        if not self.appear(FORGOTTEN_HALL_CHECK):
            self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
            self.dungeon_goto(forgotten_hall)
        STAGE_LIST.select_row(stage_keyword, main=self)

    def exit_dungeon(self, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(FORGOTTEN_HALL_CHECK):
                logger.info("Forgotten hall dungeon exited")
                break

            if self.appear_then_click(EXIT_DUNGEON):
                continue
            if self.appear_then_click(EXIT_CONFIRM):
                continue

    def _choose_first_character(self, skip_first_screenshot=True):
        """
        A temporary method used to choose the first character only
        """
        interval = Timer(1)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._forgotten_hall_enter_appear():
                logger.info("First character is chosen")
                break
            if interval.reached():
                self.device.click(FIRST_CHARACTER)
                interval.reset()

    def _forgotten_hall_enter_appear(self):
        # White button, with a color of (214, 214, 214)
        color = get_color(self.device.image, ENTER_FORGOTTEN_HALL_DUNGEON.area)
        return np.mean(color) > 180

    def _enter_forgotten_hall_dungeon(self, skip_first_screenshot=True):
        """
        called after team is set
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

            if interval.reached() and self._forgotten_hall_enter_appear():
                self.device.image_save()
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
            joystick.handle_map_run()
