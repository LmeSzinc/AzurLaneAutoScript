from typing import List

import cv2

from module.base.utils import crop
from module.retire.assets import (TEMPLATE_FLEET_1, TEMPLATE_FLEET_2,
                                  TEMPLATE_FLEET_3, TEMPLATE_FLEET_4,
                                  TEMPLATE_FLEET_5, TEMPLATE_FLEET_6)


class FleetClassifier:
    def __init__(self, buttons):
        self.buttons = buttons
        self.templates = {
            TEMPLATE_FLEET_1: 1,
            TEMPLATE_FLEET_2: 2,
            TEMPLATE_FLEET_3: 3,
            TEMPLATE_FLEET_4: 4,
            TEMPLATE_FLEET_5: 5,
            TEMPLATE_FLEET_6: 6
        }

    def pre_process(self, image):
        """
        Practice shows that, the following steps will lead to a better performance.
        It can distinguish the number from the background very well.
        If anyone needs to update TEMPLATE_FLEET assets, do remember to preprocess
        the image first.
        """
        # Invert
        image = ~image
        # Use only the green channel
        image[:, :, 0] = image[:, :, 2] = image[:, :, 1]
        # Graying and binarizing
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, image = cv2.threshold(image, 50, 255, cv2.THRESH_BINARY)
        # Re-invert and convert to BGR
        image = ~image
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        return image

    def scan(self, image) -> List[int]:
        """
        Using a template matching method to identify fleet.
        Performance on ultra rarity is not very good, because the flash
        will interfere with identification.
        """
        image_list = [self.pre_process(crop(image, button.area)) for button in self.buttons]

        result_list: List[int] = [self.predict(image) for image in image_list]

        return result_list

    def predict(self, image) -> int:
        """
        Try all the fleet number templates to find one that matched.
        Assuming it is not in any fleet if none matched.
        """
        for template, fleet in self.templates.items():
            if template.match(image):
                return fleet

        return 0
