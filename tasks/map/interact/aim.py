import cv2
import numpy as np

from module.base.decorator import cached_property, del_cached_property
from module.base.utils import Points, image_size, load_image
from module.config.utils import dict_to_kv
from module.logger import logger
from tasks.base.ui import UI


def inrange(image, lower=0, upper=255):
    """
    Get the coordinates of pixels in range.
    Equivalent to `np.array(np.where(lower <= image <= upper))` but faster.
    Note that this method will change `image`.

    `cv2.findNonZero()` is faster than `np.where`
    points = np.array(np.where(y > 24)).T[:, ::-1]
    points = np.array(cv2.findNonZero((y > 24).astype(np.uint8)))[:, 0, :]

    `cv2.inRange(y, 24)` is faster than `y > 24`
    cv2.inRange(y, 24, 255, dst=y)
    y = y > 24

    Returns:
        np.ndarray: Shape (N, 2)
            E.g. [[x1, y1], [x2, y2], ...]
    """
    cv2.inRange(image, lower, upper, dst=image)
    try:
        return np.array(cv2.findNonZero(image))[:, 0, :]
    except IndexError:
        # Empty result
        # IndexError: too many indices for array: array is 0-dimensional, but 3 were indexed
        return np.array([])


def subtract_blur(image, radius=3, negative=False):
    """
    If you care performance more than quality:
    - radius=3, use medianBlur
    - radius=5,7,9,11, use GaussianBlur
    - radius>11, use stackBlur (requires opencv >= 4.7.0)

    Args:
        image:
        radius:
        negative:

    Returns:
        np.ndarray:
    """
    if radius <= 3:
        blur = cv2.medianBlur(image, radius)
    elif radius <= 11:
        blur = cv2.GaussianBlur(image, (radius, radius), 0)
    else:
        blur = cv2.stackBlur(image, (radius, radius), 0)

    if negative:
        cv2.subtract(blur, image, dst=blur)
    else:
        cv2.subtract(image, blur, dst=blur)
    return blur


def remove_border(image, radius):
    """
    Paint edge pixels black.
    No returns, changes are written to `image`

    Args:
        image:
        radius:
    """
    width, height = image_size(image)
    image[:, :radius + 1] = 0
    image[:, width - radius:] = 0
    image[:radius + 1, :] = 0
    image[height - radius:, :] = 0


def create_circle(min_radius, max_radius):
    """
    Create a circle with min_radius <= R <= max_radius.
    1 represents circle, 0 represents background

    Args:
        min_radius:
        max_radius:

    Returns:
        np.ndarray:
    """
    circle = np.ones((max_radius * 2 + 1, max_radius * 2 + 1), dtype=np.uint8)
    center = np.array((max_radius, max_radius))
    points = np.array(np.meshgrid(np.arange(circle.shape[0]), np.arange(circle.shape[1]))).T
    distance = np.linalg.norm(points - center, axis=2)
    circle[distance < min_radius] = 0
    circle[distance > max_radius] = 0
    return circle


def draw_circle(image, circle, points):
    """
    Add a circle onto image.
    No returns, changes are written to `image`

    Args:
        image:
        circle: Created from create_circle()
        points: (x, y), center of the circle to draw
    """
    width, height = image_size(circle)
    x1 = -int(width // 2)
    y1 = -int(height // 2)
    x2 = width + x1
    y2 = height + y1
    for point in points:
        x, y = point
        # Fancy index is faster
        index = image[y + y1:y + y2, x + x1:x + x2]
        # print(index.shape)
        cv2.add(index, circle, dst=index)


class Aim:
    radius_enemy = (24, 25)
    radius_item = (8, 10)

    def __init__(self):
        self.debug = False

        self.draw_item = None
        self.draw_enemy = None
        self.points_item = None
        self.points_enemy = None

    def clear_image_cache(self):
        self.draw_item = None
        self.draw_enemy = None
        self.points_item = None
        self.points_enemy = None
        del_cached_property(self, 'aimed_enemy')
        del_cached_property(self, 'aimed_item')

    @cached_property
    def mask_interact(self):
        return load_image('./assets/mask/MASK_MAP_INTERACT.png')

    @cached_property
    def circle_enemy(self):
        return create_circle(*self.radius_enemy)

    @cached_property
    def circle_item(self):
        return create_circle(*self.radius_item)

    # @timer
    def predict_enemy(self, h, v):
        min_radius, max_radius = self.radius_enemy
        width, height = image_size(v)

        # Get white circle `y`
        y = subtract_blur(h, 3, negative=False)
        cv2.inRange(h, 168, 255, h)
        cv2.bitwise_and(y, h, dst=y)
        # Get red glow `v`
        cv2.inRange(v, 168, 255, dst=v)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cv2.dilate(v, kernel, dst=v)
        # Remove noise and leave red circle only
        cv2.bitwise_and(y, v, dst=y)
        # cv2.imshow('predict_enemy', y)
        # Remove game UI
        cv2.bitwise_and(y, self.mask_interact, dst=y)
        # Remove points on the edge, or draw_circle() will overflow
        remove_border(y, max_radius)

        # Get all pixels
        points = inrange(y, lower=18)
        if points.shape[0] > 1000:
            logger.warning(f'AimDetector.predict_enemy() too many points to draw: {points.shape}')
        # Draw circles
        draw = np.zeros((height, width), dtype=np.uint8)
        draw_circle(draw, self.circle_enemy, points)
        if self.debug:
            self.draw_enemy = cv2.multiply(draw, 4)
        draw = subtract_blur(draw, 3)

        # Find peaks
        points = inrange(draw, lower=36)
        points = Points(points).group(threshold=10)
        if points.shape[0] > 3:
            logger.warning(f'AimDetector.predict_enemy() too many peaks: {points.shape}')
        self.points_enemy = points
        # print(points)
        return points

    # @timer
    def predict_item(self, v):
        min_radius, max_radius = self.radius_item
        width, height = image_size(v)

        # Get white circle `y`
        y = subtract_blur(v, 9)
        white = cv2.inRange(v, 112, 144)
        cv2.bitwise_and(y, white, dst=y)
        # Get cyan glow `v`
        cv2.inRange(v, 0, 84, dst=v)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cv2.dilate(v, kernel, dst=v)

        # Remove noise and leave cyan circle only
        cv2.bitwise_and(y, v, dst=y)
        # Remove game UI
        cv2.bitwise_and(y, self.mask_interact, dst=y)
        # Remove points on the edge, or draw_circle() will overflow
        remove_border(y, max_radius)

        # Get all pixels
        points = inrange(y, lower=18)
        # print(points.shape)
        if points.shape[0] > 1000:
            logger.warning(f'AimDetector.predict_item() too many points to draw: {points.shape}')
        # Draw circles
        draw = np.zeros((height, width), dtype=np.uint8)
        draw_circle(draw, self.circle_item, points)
        if self.debug:
            self.draw_item = cv2.multiply(draw, 2)

        # Find peaks
        points = inrange(draw, lower=64)
        points = Points(points).group(threshold=10)
        if points.shape[0] > 3:
            logger.warning(f'AimDetector.predict_item() too many peaks: {points.shape}')
        self.points_item = points
        # print(points)
        return points

    # @timer
    def predict(self, image, enemy=True, item=True, show_log=True, debug=False):
        """
        Predict `aim` on image, costs about 10.0~10.5ms.

        Args:
            image:
            enemy: True to predict enemy
            item: True to predict item
            show_log:
            debug: True to show AimDetector image
        """
        self.debug = debug
        self.clear_image_cache()
        if isinstance(image, str):
            image = load_image(image)

        # 1.5~2.0ms
        yuv = cv2.cvtColor(image, cv2.COLOR_RGB2YUV)
        v = yuv[:, :, 2]
        h = yuv[:, :, 0]
        # 4.0~4.5ms
        if enemy:
            self.predict_enemy(h.copy(), v.copy())
        # 3.0~3.5ms
        if item:
            self.predict_item(v.copy())

        if show_log:
            kv = {}
            if self.aimed_enemy:
                kv['enemy'] = self.aimed_enemy
            if self.aimed_item:
                kv['item'] = self.aimed_item
            if kv:
                logger.info(f'Aimed: {dict_to_kv(kv)}')
        if debug:
            self.show_aim()

    def show_aim(self):
        if self.draw_enemy is None:
            if self.draw_item is None:
                return
            else:
                r = g = b = self.draw_item
        else:
            if self.draw_item is None:
                r = g = b = self.draw_enemy
            else:
                r = self.draw_enemy
                g = b = self.draw_item

        image = cv2.merge([b, g, r])

        cv2.imshow('AimDetector', image)
        cv2.waitKey(1)

    @cached_property
    def aimed_enemy(self) -> tuple[int, int] | None:
        if self.points_enemy is None:
            return None
        try:
            _ = self.points_enemy[1]
            logger.warning(f'Multiple aimed enemy found, using first point of {self.points_enemy}')
        except IndexError:
            pass
        try:
            point = self.points_enemy[0]
            return tuple(point)
        except IndexError:
            return None

    @cached_property
    def aimed_item(self) -> tuple[int, int] | None:
        if self.points_item is None:
            return None
        try:
            _ = self.points_item[1]
            logger.warning(f'Multiple aimed item found, using first point of {self.points_item}')
        except IndexError:
            pass
        try:
            point = self.points_item[0]
            return tuple(point)
        except IndexError:
            return None


class AimDetectorMixin(UI):
    @cached_property
    def aim(self):
        return Aim()


if __name__ == '__main__':
    """
    Test
    """
    self = AimDetectorMixin('src')
    self.device.disable_stuck_detection()

    while 1:
        self.device.screenshot()
        self.aim.predict(self.device.image, debug=True)
