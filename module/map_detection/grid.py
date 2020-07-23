import numpy as np

from module.base.utils import area_pad
from module.map_detection.grid_info import GridInfo
from module.map_detection.grid_predictor import GridPredictor


class Grid(GridInfo, GridPredictor):
    def __init__(self, location, image, corner, config):
        """

        Args:
            location(tuple):
            image:
            corner: (x0, y0)  +-------+  (x1, y1)
                             /         \
                            /           \
                 (x2, y2)  +-------------+  (x3, y3)
        """
        self.location = location
        super().__init__(location, image, corner, config)

    @property
    def button(self):
        """
        Returns:
            tuple: area
        """
        x0, y0, x1, y1, x2, y2, x3, y3 = self.corner.flatten()
        area = tuple(np.rint((max(x0, x2), max(y0, y1), min(x1, x3), min(y2, y3))).astype(int))
        return area_pad(area, pad=25)

    @property
    def avoid_area(self):
        x0, y0, x1, y1, x2, y2, x3, y3 = self.corner
        area = tuple(np.rint((min(x0, x2), min(y0, y1), max(x1, x3), max(y2, y3))).astype(int))
        return area_pad(area, pad=-25)
