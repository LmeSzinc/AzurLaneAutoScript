from module.base.utils import *
from module.map.map_base import CampaignMap, camera_2d
from module.map_detection.os_grid import OSGridInfo


class OSCampaignMap(CampaignMap):
    def __init__(self, name=None):
        super().__init__(name)
        self.camera_sight = (-4, -1, 3, 3)

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, scale):
        self._shape = node2location(scale.upper())
        for y in range(self._shape[1] + 1):
            for x in range(self._shape[0] + 1):
                grid = OSGridInfo()
                grid.location = (x, y)
                self.grids[(x, y)] = grid

        # camera_data can be generate automatically, but it's better to set it manually.
        self.camera_data = [location2node(loca) for loca in camera_2d((0, 0, *self._shape), sight=self.camera_sight)]
        self.camera_data_spawn_point = []
        # weight_data set to 10.
        for grid in self:
            grid.weight = 10.

    def update(self, grids, camera, mode='normal'):
        """
        Args:
            grids:
            camera (tuple):
            mode (str): Scan mode, such as 'normal', 'carrier', 'movable'
        """
        offset = np.array(camera) - np.array(grids.center_loca)
        grids.show()

        for grid in grids.grids.values():
            loca = tuple(offset + grid.location)
            if loca in self.grids:
                self.grids[loca].merge(grid)
