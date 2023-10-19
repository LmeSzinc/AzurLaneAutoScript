from module.base.decorator import cached_property
from module.map_detection.grid_info import GridInfo
from module.map_detection.grid_predictor import GridPredictor
from module.map_detection.utils import trapezoid2area


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

    @cached_property
    def inner(self):
        """
        The largest rectangle inscribed in trapezoid.

        Returns:
            tuple[int]: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        """
        return trapezoid2area(self.corner, pad=5)

    @cached_property
    def outer(self):
        """
        The smallest rectangle circumscribed by the trapezoid.

        Returns:
            tuple[int]: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        """
        return trapezoid2area(self.corner, pad=-5)

    @cached_property
    def button(self):
        """
        Expose `button` attribute, making Grid object clickable.
        """
        return self.inner
