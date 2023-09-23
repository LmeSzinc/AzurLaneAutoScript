import os

import numpy as np
from PIL import Image

from module.base.utils import load_image


class ResourceConst:
    SRCMAP = ''

    # Hard-coded coordinates under 1280x720
    MINIMAP_CENTER = (39 + 78, 48 + 78)
    MINIMAP_RADIUS = 78
    POSITION_RADIUS = 75

    # Downscale GIMAP and minimap for faster run
    POSITION_SEARCH_SCALE = 0.5
    # Search the area that is 1.666x minimap, about 100px in wild on GIMAP
    POSITION_SEARCH_RADIUS = 1.666
    # Can't figure out why but the result_of_0.5_lookup_scale + 0.5 ~= result_of_1.0_lookup_scale
    POSITION_MOVE_PATCH = (0.5, 0.5)
    # Position starting from the upper-left corner of the template image
    # but search an area larger than map
    # MINIMAP_RADIUS * POSITION_SEARCH_RADIUS * <max_scale>
    # POSITION_FEATURE_PAD = int(MINIMAP_RADIUS * POSITION_SEARCH_RADIUS * 1.5)
    POSITION_FEATURE_PAD = 155
    # Must be odd, equals int(9 * POSITION_SEARCH_SCALE) + 1
    POSITION_AREA_DILATE = 5

    # Radius to search direction arrow, about 12px
    DIRECTION_RADIUS = 12
    # Downscale direction arrows for faster run
    DIRECTION_SEARCH_SCALE = 0.5
    # Scale to 1280x720
    DIRECTION_ROTATION_SCALE = 1.0
    # Color of the direction arrow
    DIRECTION_ARROW_COLOR = (2, 199, 255)

    # Downscale GIMAP to run faster
    BIGMAP_SEARCH_SCALE = 0.25
    # Magic number that resize a 1280x720 screenshot to GIMAP_luma_05x_ps
    BIGMAP_POSITION_SCALE = 0.6137
    BIGMAP_POSITION_SCALE_ENKANOMIYA = 0.6137 * 0.7641
    # Pad 600px, cause camera sight in game is larger than GIMAP
    BIGMAP_BORDER_PAD = int(600 * BIGMAP_SEARCH_SCALE)

    # Swipe 400px is about 85~90 degree
    # <rotation_diff> * ROTATION_SWIPE_MULTIPLY = <distance_to_swipe>
    ROTATION_SWIPE_MULTIPLY = 400 / 85
    # Max distance in one swipe, limited in -600px~600px
    ROTATION_SWIPE_MAX_DISTANCE = 600

    def __init__(self):
        # Usually to be 0.4~0.5
        self.position_similarity = 0.
        # Usually > 0.05
        self.position_similarity_local = 0.
        # Current position on GIMAP with an error of about 0.1 pixel
        self.position: tuple[float, float] = (0, 0)
        # Minimap scale factor, 1.0~1.25
        self.position_scale = 1.0

        # Usually > 0.3
        # Warnings will be logged if similarity <= 0.8
        self.direction_similarity = 0.
        # Current character direction with an error of about 0.1 degree
        self.direction: float = 0.

        # Usually > 0.9
        self.rotation_confidence = 0.
        # Current cameta rotation with an error of about 1 degree
        self.rotation: int = 0

        # Usually to be 0.4~0.5
        self.bigmap_similarity = 0.
        # Usually > 0.05
        self.bigmap_similarity_local = 0.
        # Current position on GIMAP with an error of about 0.1 pixel
        self.bigmap: tuple[float, float] = (0, 0)

    def filepath(self, path: str) -> str:
        return os.path.abspath(os.path.join(self.SRCMAP, path))

    def load_image(self, file):
        if os.path.isabs(file):
            return load_image(file)
        else:
            return load_image(self.filepath(file))

    def save_image(self, image, file):
        file = self.filepath(file)
        print(f'Save image: {file}')
        Image.fromarray(image).save(file)

    def position_diff(self, target):
        """
        Args:
            target: Target position (x, y)

        Returns:
            float: Distance to current position
        """
        diff = np.linalg.norm(np.subtract(target, self.position))
        diff = round(diff, 3)
        return diff

    def is_position_near(self, target, threshold=5):
        return self.position_diff(target) <= threshold

    def position2direction(self, target):
        """
        Args:
            target: Target position (x, y)

        Returns:
            float: Direction from current position to target position (0~360)
        """
        diff = np.subtract(target, self.position)
        theta = np.rad2deg(np.arccos(-diff[1] / np.linalg.norm(diff)))
        if diff[0] < 0:
            theta = 360 - theta
        theta = round(theta, 3)
        return theta

    def direction_diff(self, target):
        """
        Args:
            target: Target degree (0~360)

        Returns:
            float: Diff to current direction (-180~180)
        """
        return diff_to_180_180(self.direction - target)

    def is_direction_near(self, target, threshold=15):
        return abs(self.direction_diff(target)) <= threshold

    def rotation_diff(self, target):
        """
        Args:
            target: Target degree (0~360)

        Returns:
            float: Diff to current rotation (-180~180)
        """
        return diff_to_180_180(self.rotation - target)

    def is_rotation_near(self, target, threshold=10):
        return abs(self.rotation_diff(target)) <= threshold


def diff_to_180_180(diff):
    """
    Args:
        diff: Degree diff

    Returns:
        float: Degree diff (-180~180)
    """
    diff = diff % 360
    if diff > 180:
        diff -= 360
    return round(diff, 3)


def diff_to_0_360(diff):
    """
    Args:
        diff: Degree diff

    Returns:
        float: Degree diff (0~360)
    """
    return round(diff % 360, 3)
