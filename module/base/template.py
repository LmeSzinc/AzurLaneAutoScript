import os

import cv2
import imageio
import numpy as np
from PIL import Image

import module.config.server as server
from module.base.decorator import cached_property


class Template:
    def __init__(self, file):
        """
        Args:
            file (dict[str], str): Filepath of template file.
        """
        self.server = server.server
        self.file = file[self.server] if isinstance(file, dict) else file
        self.is_gif = os.path.splitext(self.file)[1] == '.gif'
        self._image = None

    @property
    def image(self):
        if self._image is None:
            if self.is_gif:
                self._image = []
                for image in imageio.mimread(self.file):
                    image = image[:, :, :3] if len(image.shape) == 3 else image
                    self._image += [image, cv2.flip(image, 1)]
            else:
                self._image = np.array(Image.open(self.file))

        return self._image

    @image.setter
    def image(self, value):
        self._image = value

    @cached_property
    def size(self):
        if self.is_gif:
            return self.image[0].shape[0:2][::-1]
        else:
            return self.image.shape[0:2][::-1]

    def match(self, image, similarity=0.85):
        """
        Args:
            image:
            similarity (float): 0 to 1.

        Returns:
            bool: If matches.
        """
        if self.is_gif:
            image = np.array(image)
            for template in self.image:
                res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
                _, sim, _, _ = cv2.minMaxLoc(res)
                # print(self.file, sim)
                if sim > similarity:
                    return True

            return False

        else:
            res = cv2.matchTemplate(np.array(image), self.image, cv2.TM_CCOEFF_NORMED)
            _, sim, _, _ = cv2.minMaxLoc(res)
            # print(self.file, sim)
            return sim > similarity

    def match_result(self, image):
        """
        Args:
            image:

        Returns:
            bool: If matches.
        """
        res = cv2.matchTemplate(np.array(image), self.image, cv2.TM_CCOEFF_NORMED)
        _, sim, _, point = cv2.minMaxLoc(res)
        # print(self.file, sim)
        return sim, point

    def match_multi(self, image, similarity=0.85):
        """
        Args:
            image:
            similarity (float): 0 to 1.

        Returns:
            np.ndarray: np.array([[x0, y0], [x1, y1])
        """
        if self.is_gif:
            result = []
            image = np.array(image)
            for template in self.image:
                res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
                res = np.array(np.where(res > similarity)).T[:, ::-1].tolist()
                result += res

            return result

        else:
            result = cv2.matchTemplate(np.array(image), self.image, cv2.TM_CCOEFF_NORMED)
            result = np.array(np.where(result > similarity)).T[:, ::-1]

            return result
