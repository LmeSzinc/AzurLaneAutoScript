import numpy as np

from module.base.utils import area_pad
from module.map.grid_info import GridInfo
from module.map.grid_predictor import GridPredictor


class Grid(GridPredictor, GridInfo):
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
        self.corner = corner.flatten()

    @property
    def button(self):
        """
        Returns:
            tuple: area
        """
        x0, y0, x1, y1, x2, y2, x3, y3 = self.corner
        area = tuple(np.rint((max(x0, x2), max(y0, y1), min(x1, x3), min(y2, y3))).astype(int))
        return area_pad(area, pad=25)

    @property
    def avoid_area(self):
        x0, y0, x1, y1, x2, y2, x3, y3 = self.corner
        area = tuple(np.rint((min(x0, x2), min(y0, y1), max(x1, x3), max(y2, y3))).astype(int))
        return area_pad(area, pad=-25)
