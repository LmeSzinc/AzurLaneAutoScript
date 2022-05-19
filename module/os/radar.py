from module.base.mask import Mask
from module.base.utils import *
from module.config.config import AzurLaneConfig
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.map_detection.utils import fit_points

MASK_RADAR = Mask('./assets/mask/MASK_OS_RADAR.png')


class RadarGrid:
    is_enemy = False  # Red gun
    is_resource = False  # green box to get items
    is_exclamation = False  # Yellow exclamation mark '!'
    is_meowfficer = False  # Blue meowfficer
    is_question = False  # White question mark '?'
    is_ally = False  # Ally cargo ship in daily mission, yellow '!' on radar
    is_akashi = False  # White question mark '?'
    is_archive = False  # Purple archive
    is_port = False

    enemy_scale = 0
    enemy_genre = None  # Light, Main, Carrier, Treasure, Enemy(unknown)

    is_fleet = False

    dic_encode = {
        'EN': 'is_enemy',
        'RE': 'is_resource',
        'AR': 'is_archive',
        'EX': 'is_exclamation',
        'ME': 'is_meowfficer',
        'PO': 'is_port',
        'QU': 'is_question',
        'FL': 'is_fleet',
    }

    def __init__(self, location, image, center, config):
        """
        Args:
            location (tuple): (x, y), Grid location relative to radar center, such as (3, 2)
            image: Screenshot
            center (tuple): (x, y), the center grid center in pixel, such as (1099, 238)
            config (AzurLaneConfig):
        """
        self.location = location
        self.image: np.ndarray = image
        self.center = center
        self.config = config
        self.is_fleet = np.sum(np.abs(location)) == 0

    def encode(self):
        """
        Returns:
            str:
        """
        for key, value in self.dic_encode.items():
            if self.__getattribute__(value):
                return key

        return '--'

    @property
    def str(self):
        return self.encode()

    def reset(self):
        self.is_enemy = False
        self.is_resource = False
        self.is_exclamation = False
        self.is_meowfficer = False
        self.is_question = False
        self.is_port = False

        self.is_ally = False
        self.is_akashi = False

        self.enemy_scale = 0
        self.enemy_genre = None

        # self.is_fleet = False

    def predict(self):
        if self.is_fleet:
            return False

        self.is_enemy = self.predict_enemy() or self.predict_boss()
        self.is_resource = self.predict_resource()
        self.is_meowfficer = self.predict_meowfficer()
        self.is_exclamation = self.predict_exclamation()
        self.is_port = self.predict_port()
        self.is_question = self.predict_question()
        self.is_archive = self.predict_archive()

        if self.enemy_genre:
            self.is_enemy = True
        if self.enemy_scale:
            self.is_enemy = True
        # if not self.is_enemy:
        #     self.is_enemy = self.predict_static_red_border()
        if self.is_enemy and not self.enemy_genre:
            self.enemy_genre = 'Enemy'
        if self.config.MAP_HAS_SIREN:
            if self.enemy_genre is not None and self.enemy_genre.startswith('Siren'):
                self.is_siren = True
                self.enemy_scale = 0

    def image_color_count(self, area, color, threshold=221, count=50):
        """
        Args:
            area (tuple): Area relative to center
            color (tuple): RGB.
            threshold: 255 means colors are the same, the lower the worse.
            count (int): Pixels count.

        Returns:
            bool:
        """
        image = crop(self.image, area_offset(area, self.center))
        mask = color_similarity_2d(image, color=color) > threshold
        return np.sum(mask) > count

    def predict_enemy(self):
        return self.image_color_count(area=(-3, -3, 3, 3), color=(247, 89, 49), threshold=221, count=10)

    def predict_resource(self):
        return self.image_color_count(area=(-3, -3, 3, 3), color=(66, 231, 165), threshold=221, count=10)

    def predict_meowfficer(self):
        return self.image_color_count(area=(-3, 0, 3, 6), color=(33, 186, 255), threshold=221, count=10)

    def predict_exclamation(self):
        return self.image_color_count(area=(-3, -3, 3, 3), color=(255, 203, 49), threshold=221, count=10)

    def predict_boss(self):
        return self.image_color_count(area=(-3, -3, 3, 3), color=(147, 12, 8), threshold=221, count=10)

    def predict_port(self):
        return self.image_color_count(area=(-3, -3, 3, 3), color=(255, 255, 255), threshold=235, count=10)

    def predict_question(self):
        return self.image_color_count(area=(0, -7, 6, 0), color=(255, 255, 255), threshold=235, count=10)

    def predict_archive(self):
        return self.image_color_count(area=(-3, -3, 3, 3), color=(173, 113, 255), threshold=235, count=10)


class Radar:
    grids: dict
    center_loca = (0, 0)
    port_loca = (0, 0)

    def __init__(self, config, center=(1140, 226), delta=(11.7, 11.7), radius=5.15):
        """
        Args:
            config:
            center:
            delta:
            radius:
        """
        self.grids = {}
        self.config = config
        self.center = center
        self.delta = delta

        center = np.array(center)
        delta = np.array(delta)
        radius_int = int(radius)
        self.shape = [[-radius_int, radius_int + 1], [-radius_int, radius_int + 1]]
        for x in range(*self.shape[0]):
            for y in range(*self.shape[1]):
                if np.linalg.norm([x, y]) > radius:
                    continue
                grid_center = np.round(delta * (x, y) + center).astype(np.int)
                self.grids[(x, y)] = RadarGrid(location=(x, y), image=None, center=grid_center, config=self.config)

    def __iter__(self):
        return iter(self.grids.values())

    def __getitem__(self, item):
        """
        Returns:
            RadarGrid:
        """
        return self.grids[tuple(item)]

    def __contains__(self, item):
        return tuple(item) in self.grids

    def show(self):
        for y in range(*self.shape[1]):
            text = ' '.join([self[(x, y)].str if (x, y) in self else '  ' for x in range(*self.shape[0])])
            logger.info(text)

    def predict(self, image):
        """
        Args:
            image:

        Returns:

        """
        image = MASK_RADAR.apply(image)
        for grid in self:
            grid.image = image
            grid.reset()
            grid.predict()

    def select(self, **kwargs):
        """
        Args:
            **kwargs: Attributes of Grid.

        Returns:
            SelectedGrids:
        """
        result = []
        for grid in self:
            flag = True
            for k, v in kwargs.items():
                if grid.__getattribute__(k) != v:
                    flag = False
            if flag:
                result.append(grid)

        return SelectedGrids(result)

    def predict_port_outside(self, image):
        """
        Args:
            image: Screenshot.

        Returns:
            np.ndarray: Coordinate of the center of port icon, relative to radar center.
                Such as [57.70732954 50.89636818].
        """
        radius = (15, 82)
        image = crop(image, area_offset((-radius[1], -radius[1], radius[1], radius[1]), self.center))
        # image.show()
        points = np.where(color_similarity_2d(image, color=(255, 255, 255)) > 250)
        points = np.array(points).T[:, ::-1] - (radius[1], radius[1])
        distance = np.linalg.norm(points, axis=1)
        points = points[np.all([distance < radius[1], distance > radius[0]], axis=0)]
        point = fit_points(points, mod=(1000, 1000), encourage=5)
        point[point > 500] -= 1000
        self.port_loca = point
        return point

    def predict_port_inside(self, image):
        """
        Args:
            image: Screenshot.

        Returns:
            np.ndarray: Grid location of port on radar. Such as [3 -1].
        """
        self.predict(image)
        for grid in self:
            if grid.is_port:
                # Goto the nearby grid of port
                location = np.array(grid.location) - np.sign(grid.location) * (1, 1)
                self.port_loca = location
                return location

        return None

    @staticmethod
    def port_outside_to_inside(point):
        """
        Convert `predict_port_outside` result to `predict_port_inside`

        Args:
            point (np.ndarray): Coordinate of the center of port icon, relative to radar center.

        Returns:
            np.ndarray: Grid location of port on radar.
        """
        sight = (-4, -2, 3, 2)
        grids = [(x, y) for x in range(sight[0], sight[2] + 1) for y in [sight[1], sight[3]]] \
                + [(x, y) for x in [sight[0], sight[2]] for y in range(sight[1] + 1, sight[3])]
        grids = np.array([loca for loca in grids])
        distance = np.linalg.norm(grids, axis=1)
        degree = np.sum(grids * point, axis=1) / distance / np.linalg.norm(point)
        grid = grids[np.argmax(degree)]
        return grid

    def port_predict(self, image):
        """
        Args:
            image: Screenshot.

        Returns:
            np.ndarray: Grid location of port on radar, or a grid location that can approach port.
        """
        port = self.predict_port_inside(image)
        if port is None:
            port = self.port_outside_to_inside(self.predict_port_outside(image))
        return port

    def predict_akashi(self, image):
        """
        Args:
            image: Screenshot.

        Returns:
            tuple: Grid location of akashi on radar, or None if no akashi found.
        """
        self.predict(image)
        for location in [(0, 1), (-1, 0), (1, 0), (0, -1)]:
            grid = self[location]
            if grid.is_question and not grid.predict_port():
                return location

        return None

    def predict_question(self, image):
        """
        Args:
            image: Screenshot.

        Returns:
            tuple: Grid location of question mark on radar, or None if nothing found.
        """
        self.predict(image)
        for location in [(0, 1), (-1, 0), (1, 0), (0, -1), (0, -2), (0, -3)]:
            grid = self[location]
            if grid.is_question and not grid.predict_port():
                return location

        return None

    def nearest_object(self, camera_sight=(-4, -3, 3, 3)):
        """
        Args:
            camera_sight:

        Returns:
            RadarGrid: Or None if no objects
        """
        objects = []
        for grid in self:
            if grid.is_port:
                continue
            if grid.is_enemy or grid.is_resource or grid.is_meowfficer \
                    or grid.is_exclamation or grid.is_question or grid.is_archive:
                objects.append(grid)
        objects = SelectedGrids(objects).sort_by_camera_distance((0, 0))
        if not objects:
            return None

        nearest = objects[0]
        limited = point_limit(nearest.location, area=camera_sight)
        if nearest.location == limited:
            return nearest
        else:
            return self[limited]
