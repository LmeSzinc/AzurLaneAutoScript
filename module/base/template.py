import os

import imageio
from PIL import Image

import module.config.server as server
from module.base.button import Button
from module.base.decorator import cached_property
from module.base.utils import *
from module.map_detection.utils import Points


class Template:
    def __init__(self, file):
        """
        Args:
            file (dict[str], str): Filepath of template file.
        """
        self.server = server.server
        self.file = file[self.server] if isinstance(file, dict) else file
        self.name = os.path.splitext(os.path.basename(self.file))[0].upper()
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

    def _point_to_button(self, point, image=None, name=None):
        """
        Args:
            point:
            image: Pillow image. If provided, load color and image from it.
            name (str):

        Returns:
            Button:
        """
        if name is None:
            name = self.name
        area = area_offset(area=(0, 0, *self.size), offset=point)
        button = Button(area=area, color=(), button=area, name=name)
        if image is not None:
            button.load_color(image)
        return button

    def match_result(self, image, name=None):
        """
        Args:
            image:
            name (str):

        Returns:
            float: Similarity
            Button:
        """
        res = cv2.matchTemplate(np.array(image), self.image, cv2.TM_CCOEFF_NORMED)
        _, sim, _, point = cv2.minMaxLoc(res)
        # print(self.file, sim)

        button = self._point_to_button(point, image=image, name=name)
        return sim, button

    def match_multi(self, image, similarity=0.85, threshold=3, name=None):
        """
        Args:
            image:
            similarity (float): 0 to 1.
            threshold (int): Distance to delete nearby results.
            name (str):

        Returns:
            list[Button]:
        """
        raw = image
        if self.is_gif:
            result = []
            image = np.array(image)
            for template in self.image:
                res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
                res = np.array(np.where(res > similarity)).T[:, ::-1].tolist()
                result += res
        else:
            result = cv2.matchTemplate(np.array(image), self.image, cv2.TM_CCOEFF_NORMED)
            result = np.array(np.where(result > similarity)).T[:, ::-1]

        # result: np.array([[x0, y0], [x1, y1], ...)
        result = Points(result).group(threshold=threshold)
        return [self._point_to_button(point, image=raw, name=name) for point in result]
