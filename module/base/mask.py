import cv2
import numpy as np
from PIL import Image

from module.base.template import Template


class Mask(Template):
    @property
    def image(self):
        if self._image is None:
            self._image = np.array(Image.open(self.file).convert('L'))

        return self._image

    def apply(self, image):
        return cv2.bitwise_and(image, self.image)
