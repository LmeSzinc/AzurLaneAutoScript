import numpy as np
from PIL import Image

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
        # try:
        super().__init__(image, config)
        self.image = self._image_clear_ui(image)

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
                if leave[0] > 0:
                    self.left_edge = None
                if leave[-1] + 2 < len(self.vertical):
                    self.right_edge = None
                self.vertical = vertical
                self.grids = {}
                for grid in self._gen():
                    self.grids[grid.location] = grid

        self.center_grid = (
            np.where(self.vertical.distance_to_point(self.config.SCREEN_CENTER) >= 0)[0][0] - 1,
            np.where(self.horizontal.distance_to_point(self.config.SCREEN_CENTER) >= 0)[0][0] - 1
        )
        logger.info(f'           Center grid: {self.center_grid}')
        self.center_offset = self.grids[self.center_grid].screen_to_grid(self.config.SCREEN_CENTER)
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
                    grid = Grid(location=(x, y), image=self.image, corner=cross.points, config=self.config)
                    yield grid

    def show(self):
        for y in range(self.shape[1] + 1):
            text = ' '.join([self[(x, y)].str if (x, y) in self else '  ' for x in range(self.shape[0] + 1)])
            logger.info(text)

    def predict(self):
        for grid in self:
            grid.predict()

        # for grid in self:
        #     if grid.is_enemy and grid.enemy_scale == 0:
        #         import time
        #         self.image.save(f'{int(time.time()*1000)}.png')
        #         break

    def update(self, image):
        image = self._image_clear_ui(image)
        self.image = image
        for grid in self:
            grid.reset()
            grid.image = image

    def _image_clear_ui(self, image):
        if not self.config.MAP_HAS_DYNAMIC_RED_BORDER:
            return image

        new = Image.new('RGB', self.config.SCREEN_SIZE, (0, 0, 0))
        new.paste(image.crop(self.config.DETECTING_AREA), box=self.config.DETECTING_AREA, mask=self.config.UI_MASK_PIL)
        return new
