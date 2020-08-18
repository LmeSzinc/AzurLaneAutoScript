import time

from module.base.utils import *
from module.exception import MapDetectionError
from module.logger import logger
from module.map_detection.detector import MapDetector
from module.map_detection.grid import Grid
from module.map_detection.utils import *


class View(MapDetector):
    grids: dict
    shape: np.ndarray
    center_loca: tuple
    center_offset: np.ndarray
    swipe_base: np.ndarray

    def __iter__(self):
        return iter(self.grids.values())

    def __getitem__(self, item):
        return self.grids[tuple(item)]

    def __contains__(self, item):
        return tuple(item) in self.grids

    def show(self):
        for y in range(self.shape[1] + 1):
            text = ' '.join([self[(x, y)].str if (x, y) in self else '..' for x in range(self.shape[0] + 1)])
            logger.info(text)

    @staticmethod
    def _image_clear_ui(image):
        return cv2.copyTo(image, ASSETS.ui_mask_in_map)

    def load(self, image):
        """
        Args:
            image:
        """
        image = self._image_clear_ui(np.array(image))
        super().load(image)

        # Create local view map
        grids = {}
        for loca, points in self.generate():
            if area_in_area(area1=corner2area(points), area2=self.config.DETECTING_AREA):
                grids[loca] = Grid(location=loca, image=image, corner=points, config=self.config)

        # Handle grids offset
        offset = np.min(list(grids.keys()), axis=0)
        if np.sum(np.abs(offset)) > 0:
            logger.attr_align('grids_offset', tuple(offset.tolist()))
            self.grids = {}
            for loca, grid in grids.items():
                x, y = np.subtract(loca, offset)
                grid.location = (x, y)
                self.grids[(x, y)] = grid
        else:
            self.grids = grids
        self.shape = np.max(list(self.grids.keys()), axis=0)

        # Find local view center
        for loca, grid in self.grids.items():
            offset = grid.screen2grid([self.config.SCREEN_CENTER])[0].astype(int)
            points = grid.grid2screen(np.add([[0.5, 0], [-0.5, 0], [0, 0.5], [0, -0.5]], offset))
            self.swipe_base = np.array([np.linalg.norm(points[0] - points[1]), np.linalg.norm(points[2] - points[3])])
            self.center_loca = tuple(np.add(loca, offset).tolist())
            logger.attr_align('center_loca', self.center_loca)
            if self.center_loca in self:
                self.center_offset = self.grids[self.center_loca].screen2grid([self.config.SCREEN_CENTER])[0]
            else:
                x = max(self.center_loca[0] - self.shape[0], 0) if self.center_loca[0] > 0 else self.center_loca[0]
                y = max(self.center_loca[1] - self.shape[1], 0) if self.center_loca[1] > 0 else self.center_loca[1]
                self.center_offset = offset - self.center_loca
                raise MapDetectionError(f'Camera outside map: offset=({x}, {y})')
            break

    def predict(self):
        """
        Predict grid info.
        """
        start_time = time.time()
        for grid in self:
            grid.predict()
        logger.attr_align('predict', len(self.grids.keys()), front=float2str(time.time() - start_time) + 's')

    def update(self, image):
        """
        Update image to all grids.
        If camera position didn't change, no need to calculate again, updating image is enough.
        """
        image = self._image_clear_ui(np.array(image))
        self.image = image
        for grid in self:
            grid.reset()
            grid.image = image
