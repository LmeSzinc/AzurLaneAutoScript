import numpy as np
from PIL import Image
from skimage.color import rgb2hsv

from module.base.utils import color_similarity_2d
from module.config.config import AzurLaneConfig
from module.template.assets import *


class GridPredictor:
    ENEMY_SCALE_IMAGE_SIZE = (50, 50)
    ENEMY_PERSPECTIVE_IMAGE_SIZE = (50, 50)
    RED_BORDER_IGNORE_TOP = 10
    DIC_ENEMY_GENRE = {
        # 'Siren_1': TEMPLATE_SIREN_1,
        # 'Siren_2': TEMPLATE_SIREN_2,
        # 'Siren_3': TEMPLATE_SIREN_3,
        'Light': TEMPLATE_ENEMY_LIGHT,
        'Main': TEMPLATE_ENEMY_MAIN,
        'Carrier': TEMPLATE_ENEMY_CARRIER,
        'Treasure': TEMPLATE_ENEMY_TREASURE,
    }
    SIREN_TEMPLATE_LOADED = False

    def __init__(self, location, image, corner, config):
        """
        Args:
            location:
            image:
            corner:
            config (AzurLaneConfig)
        """
        self.config = config
        self.location = location
        self.image = image
        self.corner = corner.flatten()

        x0, y0, x1, y1, x2, y2, x3, y3 = self.corner
        divisor = x0 - x1 + x2 - x3
        x = (x0 * x2 - x1 * x3) / divisor
        y = (x0 * y2 - x1 * y2 + x2 * y0 - x3 * y0) / divisor
        self._image_center = np.array([x, y, x, y])
        self._image_a = (-x0 * x2 + x0 * x3 + x1 * x2 - x1 * x3) / divisor
        self._perspective = (
            (-x0 + x1) / self.ENEMY_PERSPECTIVE_IMAGE_SIZE[0],  # a
            (-x0 * x3 + x1 * x2) / (-x2 + x3) / self.ENEMY_PERSPECTIVE_IMAGE_SIZE[1],  # b
            x0,  # c
            0,  # d
            (-x0 * y2 + x1 * y2 + x2 * y0 - x3 * y0) / (-x2 + x3) / self.ENEMY_PERSPECTIVE_IMAGE_SIZE[1],  # e
            y0,  # f
            0,  # g
            ((-x0 + x1) / (-x2 + x3) - 1) / self.ENEMY_PERSPECTIVE_IMAGE_SIZE[1]  # h
        )

    def predict(self):
        self.image_transform = self.image.transform(self.ENEMY_PERSPECTIVE_IMAGE_SIZE, Image.PERSPECTIVE, self._perspective)

        self.enemy_scale = self.predict_enemy_scale()
        self.enemy_genre = self.predict_enemy_genre()

        self.is_mystery = self.predict_mystery()
        self.is_fleet = self.predict_fleet()
        if self.is_fleet:
            self.is_current_fleet = self.predict_current_fleet()
        self.is_boss = self.predict_boss()

        if self.config.MAP_HAS_DYNAMIC_RED_BORDER:
            if not self.is_enemy and not self.is_mystery:
                if self.predict_dynamic_red_border():
                    self.enemy_genre = 'Siren_unknown'
        self.is_caught_by_siren = self.predict_siren_caught()

        if self.enemy_genre:
            self.is_enemy = True
        if self.enemy_scale:
            self.is_enemy = True
        if not self.is_enemy:
            self.is_enemy = self.predict_static_red_border()
        if self.is_enemy and not self.enemy_genre:
            self.enemy_genre = 'Enemy'
        if self.config.MAP_HAS_SIREN:
            if self.enemy_genre is not None and self.enemy_genre.startswith('Siren'):
                self.is_siren = True
                self.enemy_scale = 0

        # self.image_perspective = color_similarity_2d(
        #     self.image.transform(self.ENEMY_PERSPECTIVE_IMAGE_SIZE, Image.PERSPECTIVE, self._perspective)
        #     , color=(255, 36, 82)
        # )

    def get_relative_image(self, relative_location, output_shape=None):
        """

        Args:
            relative_location(tuple): upper_left_x, upper_left_y, bottom_right_x, bottom_right_y
                (-1, -1, 1, 1)
            output_shape(tuple): (x, y)

        Returns:
            PIL.Image.Image
        """
        area = self._image_center + np.array(relative_location) * self._image_a
        area = tuple(np.rint(area).astype(int))
        image = self.image.crop(area)
        if output_shape is not None:
            image = image.resize(output_shape)
        return image

    def predict_enemy_scale(self):
        """
        icon on the upperleft which shows enemy scale: Large Middle Small.

        Returns:
            int: 1: Small, 2: Middle, 3: Large.
        """
        # if not self.is_enemy:
        #     return 0

        image = self.get_relative_image((-0.415 - 0.7, -0.62 - 0.7, -0.415, -0.62))
        image = np.stack(
            [
                color_similarity_2d(image, (255, 130, 132)),
                color_similarity_2d(image, (255, 239, 148)),
                color_similarity_2d(image, (255, 235, 156))
            ], axis=2
        )
        image = Image.fromarray(image).resize(self.ENEMY_SCALE_IMAGE_SIZE)

        if TEMPLATE_ENEMY_L.match(image):
            scale = 3
        elif TEMPLATE_ENEMY_M.match(image):
            scale = 2
        elif TEMPLATE_ENEMY_S.match(image):
            scale = 1
        else:
            scale = 0

        return scale

    def predict_static_red_border(self):
        # image = self.image.transform(self.ENEMY_PERSPECTIVE_IMAGE_SIZE, Image.PERSPECTIVE, self._perspective)

        image = color_similarity_2d(
            self.image_transform.crop((0, self.RED_BORDER_IGNORE_TOP, *self.ENEMY_PERSPECTIVE_IMAGE_SIZE)),
            color=(255, 36, 82))

        # Image.fromarray(np.array(image).astype('uint8'), mode='RGB').save(f'{self}.png')

        count = np.sum(image > 221)
        return count > 40

    def predict_dynamic_red_border(self, pad=4):
        image = np.array(
            self.image_transform.crop((0, self.RED_BORDER_IGNORE_TOP, *self.ENEMY_PERSPECTIVE_IMAGE_SIZE))
        ).astype(float)
        r, b = image[:, :, 0], image[:, :, 2]
        image = r - b
        image[image < 0] = 0
        image[image > 255] = 255

        mask = np.ones(np.array(image.shape) - pad * 2) * -1
        mask = np.pad(mask, ((pad, pad), (pad, pad)), mode='constant', constant_values=1)
        image = image * mask
        image[r < 221] = 0
        # print(self, np.mean(image))
        return np.mean(image) > 2

    def screen_to_grid(self, point):
        a, b, c, d, e, f, g, h = self._perspective
        y = (point[1] - f) / (e - point[1] * h)
        x = (point[0] * (h * y + 1) - b * y - c) / a
        res = np.array((x, y)) / self.ENEMY_PERSPECTIVE_IMAGE_SIZE
        return res

    def grid_to_screen(self, point):
        a, b, c, d, e, f, g, h = self._perspective
        x, y = np.array(point) * self.ENEMY_PERSPECTIVE_IMAGE_SIZE
        divisor = g * x + h * y + 1
        x = (a * x + b * y + c) / divisor
        y = (d * x + e * y + f) / divisor
        return np.array((x, y))

    def _relative_image_color_count(self, area, color, output_shape=(50, 50), color_threshold=221):
        image = self.get_relative_image(area, output_shape=output_shape)
        image = color_similarity_2d(image, color=color)
        count = np.sum(image > color_threshold)
        return count

    def _relative_image_color_hue_count(self, area, h, s=None, v=None, output_shape=(50, 50)):
        image = self.get_relative_image(area, output_shape=output_shape)
        hsv = rgb2hsv(np.array(image) / 255)
        hue = hsv[:, :, 0]
        h = np.array([-1, 1]) + h
        count = (h[0] / 360 < hue) & (hue < h[1] / 360)
        if s:
            s = np.array([-1, 1]) + s
            saturation = hsv[:, :, 1]
            count &= (s[0] / 100 < saturation) & (saturation < s[1] / 100)
        if v:
            v = np.array([-1, 1]) + v
            value = hsv[:, :, 2]
            count &= (v[0] / 100 < value) & (value < v[1] / 100)

        count = np.sum(count)
        return count

    def predict_mystery(self):
        # if not self.may_mystery:
        #     return False
        # cyan question mark
        if self._relative_image_color_count(
                area=(-0.3, -2, 0.3, -0.6), color=(148, 255, 247), output_shape=(20, 50)) > 50:
            return True
        # white background
        # if self._relative_image_color_count(
        #         area=(-0.7, -1.7, 0.7, -0.3), color=(239, 239, 239), output_shape=(50, 50)) > 700:
        #     return True

        return False

    def predict_fleet(self):
        # white ammo icon
        # return self._relative_image_color_count(
        #     area=(-1, -2, -0.5, -1.5), color=(255, 255, 255), color_threshold=252) > 300
        # count = self._relative_image_color_hue_count(area=(-1, -2, -0.5, -1.5), h=(0, 360), s=(0, 5), v=(95, 100))
        # return count > 300
        image = self.get_relative_image((-1, -2, -0.5, -1.5), output_shape=self.ENEMY_SCALE_IMAGE_SIZE)
        image = color_similarity_2d(image, (255, 255, 255))
        return TEMPLATE_FLEET_AMMO.match(image)

    def predict_current_fleet(self):
        # Green arrow over head with hue around 141.
        # image = self.get_relative_image((-0.5, -3.5, 0.5, -2.5))
        # hue = rgb2hsv(np.array(image) / 255)[:, :, 0] * 360
        # count = np.sum((141 - 3 < hue) & (hue < 141 + 3))
        # return count > 1000
        count = self._relative_image_color_hue_count(
                area=(-0.5, -3.5, 0.5, -2.5), h=(141 - 3, 141 + 10), output_shape=(50, 50))
        return count > 600

    def predict_boss(self):
        # count = self._relative_image_color_count(
        #     area=(-0.55, -0.2, 0.45, 0.2), color=(255, 77, 82), color_threshold=247)
        # return count > 100

        if TEMPLATE_ENEMY_BOSS.match(
                self.get_relative_image((-0.55, -0.2, 0.45, 0.2), output_shape=(50, 20)),
                similarity=0.75):
            return True

        # 微层混合 event_20200326_cn
        if self._relative_image_color_hue_count(
                area=(0.03, -0.15, 0.63, 0.15), h=(358 - 3, 358 + 3), output_shape=(50, 20)) > 100:
            if TEMPLATE_ENEMY_BOSS.match(
                    self.get_relative_image((0.03, -0.15, 0.63, 0.15), output_shape=(50, 20)), similarity=0.7):
                return True

        return False

    def predict_siren_caught(self):
        image = self.get_relative_image((-1, -1.5, 1, 0.5), output_shape=(120, 120))
        return TEMPLATE_CAUGHT_BY_SIREN.match(image, similarity=0.6)

    def predict_enemy_genre(self):
        image = self.get_relative_image((-1, -1, 1, 0), output_shape=(120, 60))
        if not self.SIREN_TEMPLATE_LOADED:
            for name in self.config.MAP_SIREN_TEMPLATE:
                self.DIC_ENEMY_GENRE[f'Siren_{name}'] = globals().get(f'TEMPLATE_SIREN_{name}')
                self.SIREN_TEMPLATE_LOADED = True

        for name, template in self.DIC_ENEMY_GENRE.items():
            if not self.config.MAP_HAS_SIREN and name.startswith('Siren'):
                continue
            if template.match(image):
                return name

        return None
