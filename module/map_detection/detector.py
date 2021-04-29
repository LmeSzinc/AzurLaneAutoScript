import numpy as np

from module.config.config import AzurLaneConfig
from module.map_detection.homography import Homography
from module.map_detection.perspective import Perspective


class MapDetector:
    """
    Map detector wrapper
    """
    image: np.ndarray
    config: AzurLaneConfig

    left_edge: bool
    right_edge: bool
    lower_edge: bool
    upper_edge: bool

    generate: callable

    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig):
        """
        self.config = config
        self.backend = None
        self.detector_set_backend()

    def detector_set_backend(self, name=''):
        """
        Args:
            name (str): 'homography' or 'perspective'
        """
        if not name:
            name = self.config.DETECTION_BACKEND

        if name == 'homography':
            self.backend = Homography(config=self.config)
        else:
            self.backend = Perspective(config=self.config)

    def load(self, image):
        """
        Args:
            image: Shape (720, 1280, 3)
        """
        self.backend.load(image)

        self.left_edge = bool(self.backend.left_edge)
        self.right_edge = bool(self.backend.right_edge)
        self.lower_edge = bool(self.backend.lower_edge)
        self.upper_edge = bool(self.backend.upper_edge)
        self.generate = self.backend.generate
