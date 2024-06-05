import cv2
import numpy as np

from module.base.template import Template
from module.base.utils import image_channel, load_image, rgb2gray


class Mask(Template):
    @property
    def image(self):
        if self._image is None:
            image = load_image(self.file)
            if image_channel(image) == 3:
                image = rgb2gray(image)
            self._image = image

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
        mask_channel = image_channel(self.image)
        if channel == 0:
            if mask_channel == 0:
                return False
            else:
                self._image, _, _ = cv2.split(self._image)
                return True
        else:
            if mask_channel == 0:
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
        self.set_channel(image_channel(image))
        return cv2.bitwise_and(image, self.image)
