import cv2
import numpy as np
from PIL import Image


class Template:
    def __init__(self, file):
        """
        Args:
            file (str): Filepath of template file.
        """
        self.file = file
        self.image = np.array(Image.open(file))

    def match(self, image, similarity=0.85):
        """
        Args:
            image:
            similarity (float): 0 to 1.

        Returns:
            bool: If matches.
        """
        res = cv2.matchTemplate(np.array(image), self.image, cv2.TM_CCOEFF_NORMED)
        _, sim, _, _ = cv2.minMaxLoc(res)
        # print(self.file, sim)
        return sim > similarity

    def match_multi(self, image, similarity=0.85):
        """
        Args:
            image:
            similarity (float): 0 to 1.

        Returns:
            np.ndarray: np.array([[x0, y0], [x1, y1])
        """
        result = cv2.matchTemplate(np.array(image), self.image, cv2.TM_CCOEFF_NORMED)
        result = np.array(np.where(result > similarity)).T

        return result
