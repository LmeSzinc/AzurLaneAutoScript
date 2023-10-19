import re

import cv2
import numpy as np

from module.base.timer import Timer
from module.base.utils import Points, extract_white_letters
from module.logger import logger
from tasks.base.assets.assets_base_main_page import OCR_MAP_NAME
from tasks.base.main_page import OcrPlaneName
from tasks.base.page import page_rogue
from tasks.combat.interact import CombatInteract
from tasks.map.keywords import KEYWORDS_MAP_PLANE, MapPlane
from tasks.rogue.assets.assets_rogue_exit import OCR_DOMAIN_EXIT
from tasks.rogue.assets.assets_rogue_ui import BLESSING_CONFIRM
from tasks.rogue.assets.assets_rogue_weekly import ROGUE_REPORT


def area_center(area):
    """
    Get the center of an area

    Args:
        area: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y)

    Returns:
        tuple: (x, y)
    """
    x1, y1, x2, y2 = area
    return (x1 + x2) / 2, (y1 + y2) / 2


class OcrDomainExit(OcrPlaneName):
    merge_thres_x = 50

    def pre_process(self, image):
        image = extract_white_letters(image, threshold=255)
        image = cv2.merge([image, image, image])
        return image

    def detect_and_ocr(self, *args, **kwargs):
        # Try hard to lower TextSystem.box_thresh
        backup = self.model.text_detector.box_thresh
        self.model.text_detector.box_thresh = 0.2

        result = super().detect_and_ocr(*args, **kwargs)

        self.model.text_detector.box_thresh = backup
        return result

    def _match_result(
            self,
            result: str,
            keyword_classes,
            lang: str = None,
            ignore_punctuation=True,
            ignore_digit=True):
        matched = super()._match_result(result, keyword_classes, lang, ignore_punctuation, ignore_digit)

        # Name may be covered by minimap, "Domain - " is missing,
        # check keywords like "Combat"
        if matched is None:
            for domain in MapPlane.instances.values():
                domain: MapPlane = domain
                if not domain.rogue_domain:
                    continue

                name = domain._keywords_to_find(ignore_punctuation=False)[0]
                try:
                    name = re.split('[ \-—]', name)[-1]
                except IndexError:
                    pass
                if name in result:
                    return domain

        return matched


class RogueExit(CombatInteract):
    def domain_exit_interact(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_main, DUNGEON_COMBAT_INTERACT
            out: page_main
                or page_rogue if rogue cleared
        """
        logger.info(f'Domain exit interact')
        clicked = False
        confirm = Timer(1.5, count=5)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if clicked and not self.is_in_main():
                break

            if self.handle_combat_interact():
                clicked = True
                continue
            if self.handle_popup_confirm():
                confirm.reset()
                continue

        logger.info(f'Interact loading')
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_main():
                if confirm.reached():
                    logger.info('Entered another domain')
                    break
            if self.ui_page_appear(page_rogue):
                logger.info('Rogue cleared')
                break

            if self.appear(ROGUE_REPORT, interval=2):
                self.device.click(BLESSING_CONFIRM)
                continue
            if self.handle_popup_confirm():
                confirm.reset()
                continue

    @staticmethod
    def screen2direction(point):
        """
        Args:
            point: Coordinate on screenshot

        Returns:
            float: Direction to move, -180~180
        """
        screen_middle = (640.0, 360.0)
        vanish_point = np.array((640.0, 247.34))
        distant_point = np.array((1509.46, 247.34))
        name_y = 77.60
        foot_y = 621.82

        door_projection_bottom = (
            Points([point]).link(vanish_point).get_x(name_y)[0],
            foot_y,
        )
        door_bottom = (
            point[0],
            Points([door_projection_bottom]).link(vanish_point).get_y(point[0])[0],
        )
        door_distant = (
            Points([door_bottom]).link(distant_point).get_x(foot_y)[0],
            foot_y,
        )
        planar_door = (
            door_projection_bottom[0] - screen_middle[0],
            door_projection_bottom[0] - door_distant[0],
        )
        if abs(planar_door[0]) < 5:
            direction = 0
        else:
            direction = np.rad2deg(np.arctan(planar_door[0] / planar_door[1]))

        planar_door = (round(planar_door[0], 1), round(planar_door[1], 1))
        direction = round(direction, 1)
        logger.info(f'PlanarDoor: {planar_door}, direction: {direction}')
        return direction

    def predict_door_by_name(self, image) -> float | None:
        # Paint current name black
        x1, y1, x2, y2 = OCR_MAP_NAME.area
        image[y1:y2, x1:x2] = (0, 0, 0)

        ocr = OcrDomainExit(OCR_DOMAIN_EXIT)
        results = ocr.matched_ocr(image, keyword_classes=MapPlane)
        centers = [area_center(result.area) for result in results]
        logger.info(f'DomainDoor: {centers}')
        directions = [self.screen2direction(center) for center in centers]

        count = len(centers)
        if count == 0:
            logger.warning('No domain exit found')
            return None
        if count == 1:
            logger.info(f'Goto next domain: {results[0]}')
            return directions[0]

        # Doors >= 2
        for expect in [
            KEYWORDS_MAP_PLANE.Rogue_DomainBoss,
            KEYWORDS_MAP_PLANE.Rogue_DomainElite,
            KEYWORDS_MAP_PLANE.Rogue_DomainRespite,
        ]:
            for domain, direction in zip(results, directions):
                if domain == expect:
                    logger.warning('Found multiple doors but has unique domain in it')
                    logger.info(f'Goto next domain: {domain}')
                    return direction

        logger.attr('DomainStrategy', self.config.RogueWorld_DomainStrategy)
        if self.config.RogueWorld_DomainStrategy == 'occurrence':
            for expect in [
                KEYWORDS_MAP_PLANE.Rogue_DomainTransaction,
                KEYWORDS_MAP_PLANE.Rogue_DomainOccurrence,
                KEYWORDS_MAP_PLANE.Rogue_DomainEncounter,
                KEYWORDS_MAP_PLANE.Rogue_DomainCombat,
            ]:
                for domain, direction in zip(results, directions):
                    if domain == expect:
                        logger.info(f'Goto next domain: {domain}')
                        return direction
        elif self.config.RogueWorld_DomainStrategy == 'combat':
            for expect in [
                KEYWORDS_MAP_PLANE.Rogue_DomainCombat,
                KEYWORDS_MAP_PLANE.Rogue_DomainEncounter,
                KEYWORDS_MAP_PLANE.Rogue_DomainOccurrence,
                KEYWORDS_MAP_PLANE.Rogue_DomainTransaction,
            ]:
                for domain, direction in zip(results, directions):
                    if domain == expect:
                        logger.info(f'Goto next domain: {domain}')
                        return direction
        else:
            logger.error(f'Unknown domain strategy: {self.config.RogueWorld_DomainStrategy}')

        logger.error('No domain was selected, return the first instead')
        logger.info(f'Goto next domain: {results[0]}')
        return directions[0]

    def predict_door(self, skip_first_screenshot=True) -> float | None:
        timeout = Timer(3, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.error('Predict door timeout')
                return None

            direction = self.predict_door_by_name(self.device.image)
            if direction is not None:
                return direction
