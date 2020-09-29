import cv2
import numpy as np
from PIL import Image

from module.base.template import Template


def get_image_channel(image):
    """
    Args:
        image (np.ndarray):

    Returns:
        int: 0 for monochrome, 3 for RGB.
    """
    return 3 if len(image.shape) == 3 else 0


class Mask(Template):
    @property
    def image(self):
        if self._image is None:
            self._image = np.array(Image.open(self.file).convert('L'))

        return self._image

    @image.setter
    def image(self, value):
        self._image = value

    def set_channel(self, channel):
        """
        Args:
            channel (int): 0 for monochrome, 3 for RGB.

        Returns:
            bool: If changed.
        """
        image_channel = get_image_channel(self.image)
        if channel == 0:
            if image_channel == 0:
                return False
            else:
                self._image, _, _ = cv2.split(self._image)
                return True
        else:
            if image_channel == 0:
                self._image = cv2.merge([self._image] * 3)
                return True
            else:
                return False

    def apply(self, image):
        """
        Apply mask on image.

        Args:
            image:

        Returns:
            np.ndarray:
        """
        image = np.array(image)
        self.set_channel(get_image_channel(image))
        return cv2.bitwise_and(image, self.image)
