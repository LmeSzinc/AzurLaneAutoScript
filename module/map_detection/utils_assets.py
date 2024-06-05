import cv2
import numpy as np

from module.base.decorator import cached_property
from module.base.mask import Mask
from module.base.utils import crop

UI_MASK = Mask(file='./assets/mask/MASK_MAP_UI.png')
UI_MASK_OS = Mask(file='./assets/mask/MASK_OS_MAP_UI.png')
TILE_CENTER = Mask(file='./assets/map_detection/TILE_CENTER.png')
TILE_CORNER = Mask(file='./assets/map_detection/TILE_CORNER.png')
DETECTING_AREA = (123, 55, 1280, 720)


class Assets:
    @cached_property
    def ui_mask(self):
        return UI_MASK.image

    @cached_property
    def ui_mask_os(self):
        return UI_MASK_OS.image

    @cached_property
    def ui_mask_stroke(self):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        image = cv2.erode(self.ui_mask, kernel).astype('uint8')
        return image

    @cached_property
    def ui_mask_in_map(self):
        area = np.append(np.subtract(0, DETECTING_AREA[:2]), self.ui_mask.shape[::-1])
        # area = (-123, -55, 1157, 665)
        return crop(self.ui_mask, area)

    @cached_property
    def ui_mask_os_in_map(self):
        area = np.append(np.subtract(0, DETECTING_AREA[:2]), self.ui_mask.shape[::-1])
        # area = (-123, -55, 1157, 665)
        return crop(self.ui_mask_os, area)

    @cached_property
    def tile_center_image(self):
        return TILE_CENTER.image

    @cached_property
    def tile_corner_image(self):
        return TILE_CORNER.image

    @cached_property
    def tile_corner_image_list(self):
        # [upper-left, upper-right, bottom-left, bottom-right]
        return [cv2.flip(self.tile_corner_image, -1),
                cv2.flip(self.tile_corner_image, 0),
                cv2.flip(self.tile_corner_image, 1),
                self.tile_corner_image]


ASSETS = Assets()
