import numpy as np

from module.base.utils import area_in_area
from module.config.config import AzurLaneConfig
from module.logger import logger
from module.map.grid import Grid
from module.map.perspective import Perspective, Lines


class Grids(Perspective):
    def __init__(self, image, config):
        """
        Args:
            image:
            config(AzurLaneConfig):
        """
        self.image = image
        self.config = config
        # try:
        super().__init__(image, config)

        self.grids = {}
        for grid in self._gen():
            self.grids[grid.location] = grid

        # Delete stand alone grid
        keys = np.array(list(self.grids.keys()))
        mask = np.zeros(np.max(keys, axis=0) + 1)
        mask[tuple(keys.T)] = 1
        count = np.sum(mask, axis=1)
        if np.max(count) >= 4:
            leave = np.where(count > 2)[0]
            vertical = self.vertical[leave[0]:leave[-1] + 2]
            diff = len(self.vertical) - len(vertical)
            if diff > 0:
                logger.info(f'          Grids offset: {(diff, 0)}')
                self.vertical = vertical
                self.grids = {}
                for grid in self._gen():
                    self.grids[grid.location] = grid

        self.center_grid = (
            np.where(self.vertical.distance_to_point(self.config.SCREEN_CENTER) >= 0)[0][0] - 1,
            np.where(self.horizontal.distance_to_point(self.config.SCREEN_CENTER) >= 0)[0][0] - 1
        )
        logger.info(f'           Center grid: {self.center_grid}')
        self.center_offset = self.grids[self.center_grid].screen_point_to_grid_location(self.config.SCREEN_CENTER)
        self.shape = np.max(list(self.grids.keys()), axis=0)

        # self.save_error_image()
        # except:
        #     logger.warn('Perspective error')
        #     pass
        #     self.save_error_image()

    # def save(self, folder='../screenshot'):
    #     timestamp = str(int(time.time() * 1000))
        # self.image.save(os.path.join(folder, 'z_%s.png' % timestamp))
        # for grid in self.grids.values():
        #     file = os.path.join(folder, '%s_%s_%s.png' % (timestamp, grid.location[0], grid.location[1]))
        #     grid.image_icon().save(file)

    def __iter__(self):
        return iter(self.grids.values())

    def __getitem__(self, item):
        return self.grids[tuple(item)]

    def __contains__(self, item):
        return tuple(item) in self.grids

    def _gen(self):
        for x, vert in enumerate(zip(self.vertical[:-1], self.vertical[1:])):
            for y, hori in enumerate(zip(self.horizontal[:-1], self.horizontal[1:])):
                vert = Lines(np.vstack(vert), is_horizontal=False, config=self.config)
                hori = Lines(np.vstack(hori), is_horizontal=True, config=self.config)
                cross = hori.cross(vert)
                area = np.append(cross[0], cross[3])

                if area_in_area(area, self.config.DETECTING_AREA):
                    grid = Grid(location=(x, y), image=self.image, corner=cross.points)
                    yield grid

    def show(self):
        for y in range(self.shape[1] + 1):
            text = ' '.join([self[(x, y)].str if (x, y) in self else '  ' for x in range(self.shape[0] + 1)])
            logger.info(text)

    def predict(self):
        for grid in self:
            grid.predict()

    def update(self, image):
        self.image = image
        for grid in self:
            grid.image = image
