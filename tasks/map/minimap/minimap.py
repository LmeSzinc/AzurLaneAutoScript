from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np
from scipy import signal

from module.base.utils import (
    area_limit,
    area_offset,
    area_pad,
    color_similarity_2d,
    crop,
    get_bbox,
    image_size,
    rgb2yuv
)
from module.logger import logger
from tasks.map.minimap.utils import (
    convolve,
    cubic_find_maximum,
    image_center_crop,
    map_image_preprocess,
    peak_confidence
)
from tasks.map.resource.resource import MapResource


@dataclass
class PositionPredictState:
    size: Any = None
    scale: Any = None

    search_area: Any = None
    search_image: Any = None
    result_mask: Any = None
    result: Any = None

    sim: Any = None
    loca: Any = None
    local_sim: Any = None
    local_loca: Any = None
    precise_sim: Any = None
    precise_loca: Any = None

    global_loca: Any = None


class Minimap(MapResource):
    position_locked: tuple[int | float, int | float] | None = None
    direction_locked: int | float | None = None
    rotation_locked: int | float | None = None

    def init_position(
            self,
            position: tuple[int | float, int | float],
            show_log=True,
            locked=False,
    ):
        """
        Args:
            position:
            show_log:
            locked: If true, lock search area during detection
        """
        if show_log:
            if locked:
                logger.info(f"init_position: {position}, locked")
            else:
                logger.info(f"init_position: {position}")

        self.position = position

        if locked:
            self.position_locked = position
        else:
            self.position_locked = None
        self.direction_locked = None
        self.rotation_locked = None

    def lock_direction(self, degree: int | float):
        self.direction_locked = degree
        self.direction = degree
        self.direction_similarity = 0.

    def lock_rotation(self, degree: int | float):
        self.rotation_locked = degree
        self.rotation = degree
        self.rotation_confidence = 0.

    def _predict_position(self, image, scale=1.0):
        """
        Args:
            image:
            scale:

        Returns:
            PositionPredictState:
        """
        scale *= self.POSITION_SEARCH_SCALE
        local = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        size = np.array(image_size(image))

        position = self.position
        if self.position_locked is not None:
            position = self.position_locked
        if sum(position) > 0:
            search_position = np.array(position, dtype=np.int64)
            search_position += self.POSITION_FEATURE_PAD
            search_size = np.array(image_size(local)) * self.POSITION_SEARCH_RADIUS
            search_half = (search_size // 2).astype(np.int64)
            search_area = area_offset((0, 0, *(search_half * 2)), offset=-search_half)
            search_area = area_offset(search_area, offset=np.multiply(search_position, self.POSITION_SEARCH_SCALE))
            search_area = np.array(search_area).astype(np.int64)
            search_image = crop(self.assets_floor_feat, search_area, copy=False)
            result_mask = crop(self.assets_floor_outside_mask, search_area, copy=False)
        else:
            search_area = (0, 0, *image_size(local))
            search_image = self.assets_floor_feat
            result_mask = self.assets_floor_outside_mask

        # if round(scale, 5) == self.POSITION_SEARCH_SCALE * 1.0:
        #     Image.fromarray((local).astype(np.uint8)).save('local.png')
        #     Image.fromarray((search_image).astype(np.uint8)).save('search_image.png')

        # Using mask will take 3 times as long
        # mask = self.get_circle_mask(local)
        # result = cv2.matchTemplate(search_image, local, cv2.TM_CCOEFF_NORMED, mask=mask)
        result = cv2.matchTemplate(search_image, local, cv2.TM_CCOEFF_NORMED)
        result_mask = image_center_crop(result_mask, size=image_size(result))
        result[result_mask] = 0
        _, sim, _, loca = cv2.minMaxLoc(result)
        # if round(scale, 3) == self.POSITION_SEARCH_SCALE * 1.0:
        #     result[result <= 0] = 0
        #     Image.fromarray((result * 255).astype(np.uint8)).save('match_result.png')

        # Gaussian filter to get local maximum
        local_maximum = cv2.subtract(result, cv2.GaussianBlur(result, (5, 5), 0))
        _, local_sim, _, local_loca = cv2.minMaxLoc(local_maximum)
        # if round(scale, 5) == self.POSITION_SEARCH_SCALE * 1.0:
        #     local_maximum[local_maximum < 0] = 0
        #     local_maximum[local_maximum > 0.1] = 0.1
        #     Image.fromarray((local_maximum * 255 * 10).astype(np.uint8)).save('local_maximum.png')

        # Calculate the precise location using CUBIC
        # precise = crop(result, area=area_offset((-4, -4, 4, 4), offset=local_loca))
        # precise_sim, precise_loca = cubic_find_maximum(precise, precision=0.05)
        # precise_loca -= 5
        precise_loca = np.array((0, 0))
        precise_sim = result[local_loca[1], local_loca[0]]
        state = PositionPredictState(
            size=size, scale=scale,
            search_area=search_area, search_image=search_image, result_mask=result_mask, result=result,
            sim=sim, loca=loca, local_sim=local_sim, local_loca=local_loca,
            precise_sim=precise_sim, precise_loca=precise_loca,
        )

        # Location on search_image
        lookup_loca = precise_loca + local_loca + size * scale / 2
        # Location on GIMAP
        global_loca = (lookup_loca + search_area[:2]) / self.POSITION_SEARCH_SCALE
        # Can't figure out why but the result_of_0.5_lookup_scale + 0.5 ~= result_of_1.0_lookup_scale
        global_loca += self.POSITION_MOVE_PATCH
        # Move to the origin point of map
        global_loca -= self.POSITION_FEATURE_PAD

        state.global_loca = global_loca

        return state

    def _predict_precise_position(self, state):
        """
        Args:
            result (PositionPredictState):

        Returns:
            PositionPredictState
        """
        size = state.size
        scale = state.scale
        search_area = state.search_area
        result = state.result
        loca = state.loca
        local_loca = state.local_loca

        precise = crop(result, area=area_offset((-4, -4, 4, 4), offset=loca))
        precise_sim, precise_loca = cubic_find_maximum(precise, precision=0.05)
        precise_loca -= 5

        state.precise_sim = precise_sim
        state.precise_loca = precise_loca

        # Location on search_image
        lookup_loca = precise_loca + local_loca + size * scale / 2
        # Location on GIMAP
        global_loca = (lookup_loca + search_area[:2]) / self.POSITION_SEARCH_SCALE
        # Can't figure out why but the result_of_0.5_lookup_scale + 0.5 ~= result_of_1.0_lookup_scale
        global_loca += self.POSITION_MOVE_PATCH
        # Move to the origin point of map
        global_loca -= self.POSITION_FEATURE_PAD

        state.global_loca = global_loca

        return state

    def update_position(self, image):
        """
        Get position on GIMAP, costs about 6.57ms.

        The following attributes will be set:
        - position_similarity
        - position
        - position_scene
        """
        image = self.get_minimap(image, self.POSITION_RADIUS)
        image = map_image_preprocess(image)
        image &= self.get_circle_mask(image)

        best_sim = -1.
        best_scale = 1.0
        best_state = None
        # Walking is in scale 1.20
        # Running is in scale 1.25
        scale_list = [1.00, 1.05, 1.10, 1.15, 1.20, 1.25]

        for scale in scale_list:
            state = self._predict_position(image, scale)
            # print([np.round(i, 3) for i in [scale, state.sim, state.local_sim, state.global_loca]])
            if state.sim > best_sim:
                best_sim = state.sim
                best_scale = scale
                best_state = state

        best_state = self._predict_precise_position(best_state)

        self.position_similarity = round(best_state.precise_sim, 3)
        self.position_similarity_local = round(best_state.local_sim, 3)
        self.position = tuple(np.round(best_state.global_loca, 1))
        self.position_scale = round(best_scale, 3)
        return self.position

    def update_direction(self, image):
        """
        Get direction of character, costs about 0.64ms.

        The following attributes will be set:
        - direction_similarity
        - direction
        """
        image = self.get_minimap(image, self.DIRECTION_RADIUS)

        image = color_similarity_2d(image, color=self.DIRECTION_ARROW_COLOR)
        try:
            area = area_pad(get_bbox(image, threshold=128), pad=-1)
            area = area_limit(area, (0, 0, *image_size(image)))
        except IndexError:
            # IndexError: index 0 is out of bounds for axis 0 with size 0
            logger.warning('No direction arrow on minimap')
            return

        image = crop(image, area=area)
        scale = self.DIRECTION_ROTATION_SCALE * self.DIRECTION_SEARCH_SCALE
        mapping = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        result = cv2.matchTemplate(self.ArrowRotateMap, mapping, cv2.TM_CCOEFF_NORMED)
        result = cv2.subtract(result, cv2.GaussianBlur(result, (5, 5), 0))
        _, sim, _, loca = cv2.minMaxLoc(result)
        loca = np.array(loca) / self.DIRECTION_SEARCH_SCALE // (self.DIRECTION_RADIUS * 2)
        degree = int((loca[0] + loca[1] * 8) * 5)

        def to_map(x):
            return int((x * self.DIRECTION_RADIUS * 2 + self.DIRECTION_RADIUS) * self.POSITION_SEARCH_SCALE)

        # Row on ArrowRotateMapAll
        row = int(degree // 8) + 45
        # Calculate +-1 rows to get result with a precision of 1
        row = (row - 2, row + 3)
        # Convert to ArrowRotateMapAll and to be 5px larger
        row = (to_map(row[0]) - 5, to_map(row[1]) + 5)

        precise_map = self.ArrowRotateMapAll[row[0]:row[1], :]
        result = cv2.matchTemplate(precise_map, mapping, cv2.TM_CCOEFF_NORMED)
        result = cv2.subtract(result, cv2.GaussianBlur(result, (5, 5), 0))

        def to_map(x):
            return int((x * self.DIRECTION_RADIUS * 2) * self.POSITION_SEARCH_SCALE)

        def get_precise_sim(d):
            y, x = divmod(d, 8)
            im = result[to_map(y):to_map(y + 1), to_map(x):to_map(x + 1)]
            _, sim, _, _ = cv2.minMaxLoc(im)
            return sim

        precise = np.array([[get_precise_sim(_) for _ in range(24)]])
        precise_sim, precise_loca = cubic_find_maximum(precise, precision=0.1)
        precise_loca = degree // 8 * 8 - 8 + precise_loca[0]

        self.direction_similarity = round(precise_sim, 3)
        self.direction = round(precise_loca % 360, 1)

    def update_rotation(self, image):
        """
        Get direction of character, costs about 0.66ms.

        The following attributes will be set:
        - direction_similarity
        - direction
        """
        d = self.MINIMAP_RADIUS * 2
        scale = 1

        # Extract
        minimap = self.get_minimap(image, radius=self.MINIMAP_RADIUS)
        _, _, v = cv2.split(rgb2yuv(minimap))

        image = cv2.subtract(128, v)

        image = cv2.GaussianBlur(image, (3, 3), 0)
        # Expand circle into rectangle
        remap = cv2.remap(image, *self.RotationRemapData, cv2.INTER_LINEAR)[d * 1 // 10:d * 6 // 10].astype(np.float32)
        remap = cv2.resize(remap, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
        # Find derivative
        gradx = cv2.Scharr(remap, cv2.CV_32F, 1, 0)
        # import matplotlib.pyplot as plt
        # plt.imshow(gradx)
        # plt.show()

        # Magic parameters for scipy.find_peaks
        para = {
            # 'height': (50, 800),
            'height': 35,
            # 'prominence': (0, 400),
            # 'width': (0, d * scale / 20),
            # 'distance': d * scale / 18,
            'wlen': d * scale,
        }
        # plt.plot(gradx[d * 3 // 10])
        # plt.show()

        # `l` for the left of sight area, derivative is positive
        # `r` for the right of sight area, derivative is negative
        l = np.bincount(signal.find_peaks(gradx.ravel(), **para)[0] % (d * scale), minlength=d * scale)
        r = np.bincount(signal.find_peaks(-gradx.ravel(), **para)[0] % (d * scale), minlength=d * scale)
        l, r = np.maximum(l - r, 0), np.maximum(r - l, 0)
        # plt.plot(l)
        # plt.plot(np.roll(r, -d * scale // 4))
        # plt.show()

        conv0 = []
        kernel = 2 * scale
        r_expanded = np.concatenate([r, r, r])
        r_length = len(r)

        # Faster than nested calling np.roll()
        def roll_r(shift):
            return r_expanded[r_length - shift:r_length * 2 - shift]

        def convolve_r(ker, shift):
            return sum(roll_r(shift + i) * (ker - abs(i)) // ker for i in range(-ker + 1, ker))

        for offset in range(-kernel + 1, kernel):
            result = l * convolve_r(ker=3 * kernel, shift=-d * scale // 4 + offset)
            # result = l * convolve(np.roll(r, -d * scale // 4 + offset), kernel=3 * scale)
            # minus = l * convolve(np.roll(r, offset), kernel=10 * scale) // 5
            # if offset == 0:
            #     plt.plot(result)
            #     plt.plot(-minus)
            #     plt.show()
            # result -= minus
            # result = convolve(result, kernel=3 * scale)
            conv0 += [result]
        # plt.figure(figsize=(20, 16))
        # for row in conv0:
        #     plt.plot(row)
        # plt.show()

        conv0 = np.maximum(conv0, 1)
        maximum = np.max(conv0, axis=0)
        rotation_confidence = round(peak_confidence(maximum), 3)
        if rotation_confidence > 0.3:
            # Good match
            result = maximum
        else:
            # Convolve again to reduce noice
            average = np.mean(conv0, axis=0)
            minimum = np.min(conv0, axis=0)
            result = convolve(maximum * average * minimum, 2 * scale)
            rotation_confidence = round(peak_confidence(maximum), 3)
        # plt.plot(maximum)
        # plt.plot(result)
        # plt.show()

        # Convert match point to degree
        degree = np.argmax(result) / (d * scale) * 360 + 135
        degree = int(degree % 360)
        # +3 is a value obtained from experience
        # Don't know why but <predicted_rotation> + 3 = <actual_rotation>
        rotation = (degree + 3) % 360

        self.rotation_confidence = rotation_confidence
        self.rotation = rotation

    def update(self, image, show_log=True):
        """
        Update minimap, costs about 7.88ms.
        """
        self.update_position(image)
        if self.direction_locked is None:
            self.update_direction(image)
        if self.rotation_locked is None:
            self.update_rotation(image)
        if show_log:
            self.log_minimap()

    def log_minimap(self):
        # MiniMap P:(567.5, 862.8) (1.00x|0.439|0.157), D:303.8 (0.253), R:304 (0.846)
        logger.info(
            f'MiniMap '
            f'P:({self.position[0]:.1f}, {self.position[1]:.1f}) '
            f'({self.position_scale:.2f}x|{self.position_similarity:.3f}|{self.position_similarity_local:.3f}), '
            f'D:{self.direction:.1f} ({self.direction_similarity:.3f}), '
            f'R:{self.rotation} ({self.rotation_confidence:.3f})'
        )


if __name__ == '__main__':
    """
    Run mimimap tracking test.
    """
    from tasks.base.ui import UI

    # Uncomment this to use local srcmap instead of the pre-built one
    # MapResource.SRCMAP = '../srcmap/srcmap'
    self = Minimap()
    # Set plane, assume starting from Jarilo_AdministrativeDistrict
    self.set_plane('Jarilo_BackwaterPass', floor='F1')

    ui = UI('src')
    ui.device.disable_stuck_detection()
    # Set starter point. Starter point will be calculated if it's missing but may contain errors.
    # With starter point set, position is only searched around starter point and new position becomes new starter point.
    # self.init_position((337, 480))
    while 1:
        ui.device.screenshot()
        self.update(ui.device.image)
        self.show_minimap()
