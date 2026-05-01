import cv2
import numpy as np
from yaml import safe_dump

from module.base.button import Button
from module.base.mask import Mask
from module.base.utils import color_similarity_2d, rgb2luma, load_image, random_rectangle_vector, area_offset, crop
from module.island.data import DIC_ISLAND_TECHNOLOGY
from module.island.ui import IslandUI
from module.ui.page import page_island_technology

DELTA_X = 136 + 2/3
DELTA_Y = 60
ORIGIN_X = -5/3
ORIGIN_Y = 46
LEFT_STRIP = 167
MASK_ISLAND_TECHNOLOGY = Mask('./assets/mask/MASK_ISLAND_TECHNOLOGY.png')
TECHNOLOGY_LENGTH = {
    '2': 3139 - 1280 + LEFT_STRIP,
    '3': 4231 - 1280 + LEFT_STRIP,
    '4': 3003 - 1280 + LEFT_STRIP,
    '5': 5462 - 1280 + LEFT_STRIP,
    '6': 4233 - 1280 + LEFT_STRIP,
}
DETECTION_AREA = (167, 54, 1280, 720)
DETECTION_AREA_MASK = (1098, 646, 1280, 720)
BUTTON_AREA = (-110, -26, 110, 26)


def extract_flowchart(image):
    brightness = rgb2luma(image)
    black = color_similarity_2d(image, (7, 10, 17))
    brightness_mask = cv2.inRange(brightness, 160, 255)
    black_mask = cv2.inRange(black, 245, 255)
    mask = cv2.bitwise_or(brightness_mask, black_mask)
    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled_mask = np.zeros_like(mask)
    cv2.drawContours(filled_mask, contours, -1, 255, thickness=cv2.FILLED)
    filled_mask = MASK_ISLAND_TECHNOLOGY.apply(filled_mask)
    filled_mask = filled_mask[:, LEFT_STRIP:]
    return filled_mask

def get_technology_tab_and_position(index):
    tech_info = DIC_ISLAND_TECHNOLOGY[index]
    tab = tech_info['tech_belong']
    axis_x, axis_y = tech_info['axis']
    position_x = ORIGIN_X + DELTA_X * axis_x
    position_y = ORIGIN_Y + DELTA_Y * axis_y
    return tab, (position_x, position_y)

class IslandTechnologyHandler(IslandUI):
    """
    Currently only supports checking tab 2,3,4,5,6.
    """
    def get_technology_view_position(self, tab):
        globe_view = load_image(f'./assets/island/technology/technology_chart_{tab}.png')
        extracted_flowchart = extract_flowchart(self.device.image)
        result = cv2.matchTemplate(globe_view, extracted_flowchart, cv2.TM_CCOEFF_NORMED)
        _, similarity, _, loca = cv2.minMaxLoc(result)
        return loca[0]

    def _island_technology_swipe(self, forward=True):
        detection_area = DETECTION_AREA
        direction_vector = (-600, 0) if forward else (600, 0)
        p1, p2 = random_rectangle_vector(
            direction_vector, box=detection_area, random_range=(-50, -50, 50, 50), padding=20
        )
        self.device.drag(p1, p2, segments=2, shake=(0, 25), point_random=(0, 0, 0, 0), shake_random=(0, -5, 0, 5))

    def technology_reset_view(self, skip_first_screenshot=True):
        active = self._island_technology_side_navbar_get_active()
        for _ in range(10):  # tab 5 has 4400 length, so 5 swipes are not enough
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            position_x = self.get_technology_view_position(tab=active)
            if position_x < 3:
                break
            self._island_technology_swipe(forward=False)
        self.device.click_record_remove('DRAG')

    def scan_all(self):
        all_technology = {}
        for index in DIC_ISLAND_TECHNOLOGY.keys():
            if DIC_ISLAND_TECHNOLOGY[index]['tech_belong'] not in [2, 3, 4, 5, 6]:
                continue
            tab, position = get_technology_tab_and_position(index)
            all_technology[index] = {
                'tab': tab,
                'position': position,
                'active': False,
            }
        technology_by_tab = [{} for _ in range(5)]
        for index, info in all_technology.items():
            technology_by_tab[info['tab'] - 2][index] = info['position']
        for tab in range(2, 7):
            self.island_technology_side_navbar_ensure(tab=tab)
            self.technology_reset_view()
            position_x_old = None
            for _ in self.loop():
                position_x = self.get_technology_view_position(tab=tab)
                if position_x_old is not None:
                    if position_x - position_x_old < 5:
                        break
                position_x_old = position_x
                for index, (tech_pos_x, tech_pos_y) in technology_by_tab[tab - 2].items():
                    tech_pos_x_in_view = tech_pos_x - position_x
                    if (DETECTION_AREA[0] - BUTTON_AREA[0] <= LEFT_STRIP + tech_pos_x_in_view <= DETECTION_AREA[2] - BUTTON_AREA[2]
                        and not (
                            tech_pos_y > DETECTION_AREA_MASK[1] + BUTTON_AREA[1]
                            and LEFT_STRIP + tech_pos_x_in_view >= DETECTION_AREA_MASK[0]
                            )):
                        tech_button = crop(self.device.image, area=area_offset(BUTTON_AREA, (LEFT_STRIP + tech_pos_x_in_view, tech_pos_y)))
                        luma = rgb2luma(tech_button)
                        color = np.mean(luma.flatten())
                        if color > 160:
                            all_technology[index]['active'] = True
                self._island_technology_swipe(forward=True)
                self.device.click_record_remove('DRAG')
        return {index: info['active'] for index, info in all_technology.items()}

    def run(self):
        self.ui_ensure(page_island_technology)
        result = self.scan_all()
        value = safe_dump(result)
        self.config.cross_set(keys="IslandInfo.IslandTechnology.TechnologyStatus", value=value)


