import cv2
import numpy as np
from PIL import Image


class Template:
    def __init__(self, area, color, button, file):
        """
        Args:
            file(str): Relative path to file.
        """

        # self.area = image.getbbox()
        self.area = area
        self.color = color
        self.button = button
        image = Image.open(file)
        self.image = np.array(image.crop(self.area))
        self.similarity = 0.85
        self.preprocess_func = None

    def set_preprocess_func(self, func):
        """
        Args:
            func: Image preprocess function
        """
        self.preprocess_func = func
        self.image = self._preprocess(self.image)

    def _preprocess(self, image):
        image = image.astype(float)
        image = self.preprocess_func(image)
        image[image > 255] = 255
        image[image < 0] = 0
        image = image.astype('uint8')
        return image

    def match(self, image):
        """
        Args:
            image: Full-screen screenshot.

        Returns:
            bool: True if template matched.
        """
        image = np.array(image.crop(self.area))
        if self.preprocess_func is not None:
            image = self._preprocess(image)

        res = cv2.matchTemplate(np.array(image), self.image, cv2.TM_CCOEFF_NORMED)
        _, similarity, _, _ = cv2.minMaxLoc(res)

        return similarity > self.similarity


def preprocess_func_example(image):
    """
     Args:
         image (np.ndarray):

     Returns:
         np.ndarray
     """
    image = (image - 64) / 0.75
    return image
