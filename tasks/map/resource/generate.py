import os
from functools import cached_property

import cv2
import numpy as np

from module.base.utils import (
    color_similarity_2d,
    crop,
    get_bbox,
    get_bbox_reversed,
    image_paste,
    image_size
)
from module.config.utils import iter_folder
from tasks.map.minimap.utils import map_image_preprocess, rotate_bound
from tasks.map.resource.const import ResourceConst


def register_output(output):
    def register_wrapper(func):
        def wrapper(self, *args, **kwargs):
            image = func(self, *args, **kwargs)
            self.DICT_GENERATE[output] = image
            return image

        return wrapper

    return register_wrapper


class ResourceGenerator(ResourceConst):
    DICT_GENERATE = {}

    """
    Input images
    """

    @cached_property
    @register_output('./srcmap/direction/Arrow.png')
    def Arrow(self):
        return self.load_image('./resources/direction/Arrow.png')

    """
    Output images
    """

    @cached_property
    def _ArrowRorateDict(self):
        """
        Returns:

        """
        image = self.Arrow
        arrows = {}
        for degree in range(0, 360):
            rotated = rotate_bound(image, degree)
            rotated = crop(rotated, area=get_bbox(rotated, threshold=15))
            # rotated = cv2.resize(rotated, None, fx=self.ROTATE, fy=self.ROTATE, interpolation=cv2.INTER_NEAREST)
            rotated = color_similarity_2d(rotated, color=self.DIRECTION_ARROW_COLOR)
            arrows[degree] = rotated
        return arrows

    @cached_property
    @register_output('./srcmap/direction/ArrowRotateMap.png')
    def ArrowRotateMap(self):
        radius = self.DIRECTION_RADIUS
        image = np.zeros((10 * radius * 2, 9 * radius * 2), dtype=np.uint8)
        for degree in range(0, 360, 5):
            y, x = divmod(degree / 5, 8)
            rotated = self._ArrowRorateDict.get(degree)
            point = (radius + int(x) * radius * 2, radius + int(y) * radius * 2)
            # print(degree, y, x, point[0],point[0] + radius, point[1],point[1] + rotated.shape[1])
            image_paste(rotated, image, origin=point)
        image = cv2.resize(image, None,
                           fx=self.DIRECTION_SEARCH_SCALE, fy=self.DIRECTION_SEARCH_SCALE,
                           interpolation=cv2.INTER_NEAREST)
        return image

    @cached_property
    @register_output('./srcmap/direction/ArrowRotateMapAll.png')
    def ArrowRotateMapAll(self):
        radius = self.DIRECTION_RADIUS
        image = np.zeros((136 * radius * 2, 9 * radius * 2), dtype=np.uint8)
        for degree in range(360 * 3):
            y, x = divmod(degree, 8)
            rotated = self._ArrowRorateDict.get(degree % 360)
            point = (radius + int(x) * radius * 2, radius + int(y) * radius * 2)
            # print(degree, y, x, point)
            image_paste(rotated, image, origin=point)
        image = cv2.resize(image, None,
                           fx=self.DIRECTION_SEARCH_SCALE, fy=self.DIRECTION_SEARCH_SCALE,
                           interpolation=cv2.INTER_NEAREST)
        return image

    @cached_property
    def _map_background(self):
        image = self.load_image('./resources/position/background.png')
        height, width, channel = image.shape
        grid = (10, 10)

        background = np.zeros((height * grid[0], width * grid[1], channel), dtype=np.uint8)
        for y in range(grid[0]):
            for x in range(grid[1]):
                image_paste(image, background, origin=(width * x, height * y))
        background = background.copy()
        return background

    def _map_image_standardize(self, image, padding=0):
        """
        Remove existing paddings
        Map stroke color is about 127~134, background is 199~208
        """
        image = crop(image, get_bbox_reversed(image, threshold=160))
        if padding > 0:
            size = np.array((padding, padding)) * 2 + image_size(image)
            background = crop(self._map_background, area=(0, 0, *size))
            image_paste(image, background, origin=(padding, padding))
            return background
        else:
            return image

    def _map_image_extract_feat(self, image):
        """
        Extract a feature image for positioning.
        """
        image = self._map_image_standardize(image, padding=ResourceConst.POSITION_FEATURE_PAD)
        image = map_image_preprocess(image)
        scale = self.POSITION_SEARCH_SCALE
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        return image

    def _map_image_extract_area(self, image):
        """
        Extract accessible area on map.
        *.area.png has `area` in red, extract into a binary image.
        """
        # To the same size as feature map
        image = self._map_image_standardize(image, padding=ResourceConst.POSITION_FEATURE_PAD)
        image = color_similarity_2d(image, color=(255, 0, 0))
        scale = self.POSITION_SEARCH_SCALE
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        _, image = cv2.threshold(image, 180, 255, cv2.THRESH_BINARY)
        # Make the area a little bit larger
        kernel = self.POSITION_AREA_DILATE
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel, kernel))
        image = cv2.dilate(image, kernel)

        # Black area on white background
        # image = cv2.subtract(255, image)
        return image

    @cached_property
    def GernerateMapFloors(self):
        for world in iter_folder(self.filepath('./resources/position'), is_dir=True):
            world_name = os.path.basename(world)
            for floor in iter_folder(world, ext='.png'):
                print(f'Read image: {floor}')
                image = self.load_image(floor)
                floor_name = os.path.basename(floor)[:-4]
                if floor_name.endswith('.area'):
                    # ./srcmap/position/{world_name}/xxx.area.png
                    output = f'./srcmap/position/{world_name}/{floor_name}.png'
                    register_output(output)(ResourceGenerator._map_image_extract_area)(self, image)
                else:
                    output = f'./srcmap/position/{world_name}/{floor_name}.png'
                    register_output(output)(ResourceGenerator._map_image_standardize)(self, image)
                    output = f'./srcmap/position/{world_name}/{floor_name}.feat.png'
                    register_output(output)(ResourceGenerator._map_image_extract_feat)(self, image)

        # Floor images are cached already, no need to return a real value
        return True

    def generate_output(self):
        os.makedirs(self.filepath('./srcmap'), exist_ok=True)
        # Calculate all resources
        for method in self.__dir__():
            if not method.startswith('__') and not method.islower():
                _ = getattr(self, method)
        # Create output folder
        folders = set([os.path.dirname(file) for file in self.DICT_GENERATE.keys()])
        for output in folders:
            output = self.filepath(output)
            os.makedirs(output, exist_ok=True)
        # Save image
        for output, image in self.DICT_GENERATE.items():
            self.save_image(image, file=output)


if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(__file__), '../../../'))
    ResourceConst.SRCMAP = '../srcmap'
    ResourceGenerator().generate_output()
