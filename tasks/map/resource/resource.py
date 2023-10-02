import os
from functools import cached_property

import cv2
import numpy as np

from module.base.decorator import del_cached_property
from module.base.utils import area_offset, crop, image_size
from module.exception import ScriptError
from module.logger import logger
from tasks.map.minimap.utils import create_circular_mask
from tasks.map.resource.const import ResourceConst
from tasks.map.keywords import KEYWORDS_MAP_PLANE, MapPlane

SPECIAL_PLANES = [
    ('Luofu_StargazerNavalia', 'F2Rogue')
]


class MapResource(ResourceConst):
    is_special_plane: bool

    def __init__(self):
        super().__init__()

        if MapResource.SRCMAP:
            self.SRCMAP = os.path.abspath(MapResource.SRCMAP)
            logger.warning(f'MapResource.SRMAP is set to "{self.SRCMAP}", '
                           f'this should only be used in DEV environment.')
        else:
            try:
                import srcmap
                self.SRCMAP = srcmap.srcmap()
            except ImportError:
                logger.critical('Dependency "srmap" is not installed')
                raise ScriptError('Dependency "srmap" is not installed')

        # Jarilo_AdministrativeDistrict
        self.plane: MapPlane = KEYWORDS_MAP_PLANE.Herta_ParlorCar
        # Floor name in game (B1, F1, F2, ...)
        self.floor: str = 'F1'
        # Key: (width, height), mask shape
        # Value: np.ndarray, mask image
        self._dict_circle_mask = {}

    @cached_property
    def ArrowRotateMap(self):
        return self.load_image('./direction/ArrowRotateMap.png')

    @cached_property
    def ArrowRotateMapAll(self):
        return self.load_image('./direction/ArrowRotateMapAll.png')

    def set_plane(self, plane, floor='F1'):
        """
        Args:
            plane (MapPlane, str): Such as Jarilo_AdministrativeDistrict
            floor (str):
        """
        self.plane: MapPlane = MapPlane.find(plane)
        if (self.plane.name, floor) in SPECIAL_PLANES:
            self.floor = floor
            self.is_special_plane = True
        else:
            self.floor = self.plane.convert_to_floor_name(floor)
            self.is_special_plane = False

        del_cached_property(self, 'assets_file_basename')
        del_cached_property(self, 'assets_floor')
        del_cached_property(self, 'assets_floor_feat')
        del_cached_property(self, 'assets_floor_outside_mask')

    @cached_property
    def assets_file_basename(self):
        if self.plane.has_multiple_floors:
            return f'./position/{self.plane.world}/{self.plane.name}_{self.floor}'
        else:
            return f'./position/{self.plane.world}/{self.plane.name}'

    @cached_property
    def assets_floor(self):
        return self.load_image(f'{self.assets_file_basename}.png')

    @cached_property
    def assets_floor_feat(self):
        return self.load_image(f'{self.assets_file_basename}.feat.png')

    @cached_property
    def assets_floor_outside_mask(self):
        image = self.load_image(f'{self.assets_file_basename}.area.png')
        return image == 0

    def get_minimap(self, image, radius):
        """
        Crop the minimap area on image.
        """
        area = area_offset((-radius, -radius, radius, radius), offset=self.MINIMAP_CENTER)
        image = crop(image, area)
        return image

    def get_circle_mask(self, image):
        """
        Create a circle mask with the shape of given image,
        Masks will be cached once created.
        """
        w, h = image_size(image)
        try:
            return self._dict_circle_mask[(w, h)]
        except KeyError:
            mask = create_circular_mask(w=w, h=h)
            mask = (mask * 255).astype(np.uint8)
            self._dict_circle_mask[(w, h)] = mask
            return mask

    @cached_property
    def RotationRemapData(self):
        d = self.MINIMAP_RADIUS * 2
        mx = np.zeros((d, d), dtype=np.float32)
        my = np.zeros((d, d), dtype=np.float32)
        for i in range(d):
            for j in range(d):
                mx[i, j] = d / 2 + i / 2 * np.cos(2 * np.pi * j / d)
                my[i, j] = d / 2 + i / 2 * np.sin(2 * np.pi * j / d)
        return mx, my

    @cached_property
    def _named_window(self):
        return cv2.namedWindow('MinimapTracking')

    def show_minimap(self):
        image = cv2.cvtColor(self.assets_floor, cv2.COLOR_RGB2BGR)

        position = np.array(self.position).astype(int)

        def vector(degree):
            degree = np.deg2rad(degree - 90)
            point = np.array(position) + np.array((np.cos(degree), np.sin(degree))) * 30
            return point.astype(int)

        image = cv2.circle(image, position, radius=5, color=(0, 0, 255), thickness=-1)
        image = cv2.line(image, position, vector(self.direction), color=(0, 255, 0), thickness=2)
        image = cv2.line(image, position, vector(self.rotation), color=(255, 0, 0), thickness=2)
        cv2.imshow('MinimapTracking', image)
        cv2.waitKey(1)
