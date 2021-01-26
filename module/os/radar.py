from module.base.utils import *
from module.config.config import AzurLaneConfig
from module.logger import logger


class RadarGrid:
    is_enemy = False  # Red gun
    is_resource = False  # green box to get items
    is_exclamation = False  # Yellow exclamation mark '!'
    is_meowfficer = False  # Blue meowfficer
    is_question = False  # White question mark '?'
    is_ally = False  # Ally cargo ship in daily mission, yellow '!' on radar
    is_akashi = False  # White question mark '?'

    enemy_scale = 0
    enemy_genre = None  # Light, Main, Carrier, Treasure, Enemy(unknown)

    is_fleet = False

    dic_encode = {
        'EN': 'is_enemy',
        'RE': 'is_resource',
        'EX': 'is_exclamation',
        'ME': 'is_meowfficer',
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
        self.image = image
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
        self.is_ally = False
        self.is_akashi = False

        self.enemy_scale = 0
        self.enemy_genre = None

        self.is_fleet = False

    def predict(self):
        if self.is_fleet:
            return False

        self.is_enemy = self.predict_enemy() or self.predict_boss()
        self.is_resource = self.predict_resource()
        self.is_meowfficer = self.predict_meowfficer()
        self.is_exclamation = self.predict_exclamation()

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
        image = self.image.crop(area_offset(area, self.center))
        mask = color_similarity_2d(image, color=color) > threshold
        return np.sum(mask) > count

    def predict_enemy(self):
        return self.image_color_count(area=(-3, -3, 3, 3), color=(247, 89, 49), threshold=221, count=10)

    def predict_resource(self):
        return self.image_color_count(area=(-3, -3, 3, 3), color=(66, 231, 165), threshold=221, count=10)

    def predict_meowfficer(self):
        return self.image_color_count(area=(-3, -0, 3, 6), color=(33, 186, 255), threshold=221, count=10)

    def predict_exclamation(self):
        return self.image_color_count(area=(-3, -3, 3, 3), color=(255, 203, 49), threshold=221, count=10)

    def predict_boss(self):
        return self.image_color_count(area=(-3, -3, 3, 3), color=(147, 12, 8), threshold=221, count=10)


class Radar:
    grids: dict
    center_loca = (0, 0)

    def __init__(self, config, center=(1158, 226), delta=(11.7, 11.7), radius=5.15):
        """
        Args:
            config:
            center:
            delta:
            radius:
        """
        self.grids = {}
        self.config = config

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
        for grid in self:
            grid.image = image
            grid.reset()
            grid.predict()
