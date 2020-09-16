import time
import warnings

import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import signal
from scipy.misc import electrocardiogram

from module.base.decorator import cached_property
from module.base.mask import Mask
from module.base.utils import *
from module.config.config import AzurLaneConfig
from module.map_detection.utils import *
from module.template.assets import *
from module.logger import logger


DETECTING_AREA = (0, 0, 1280, 720)

EQUIP_MASK = Mask(file='./assets/mask/MASK_EQUIPMENT.png')

INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
    'height': (175, 230),
    'width': (0.9, 10),
    'prominence': 10,
    'distance': 35,
}
EDGE_LINES_FIND_PEAKS_PARAMETERS = {
    'height': (213, 230),
    'prominence': 10,
    'distance': 50,
    # 'width': (0, 7),
    'wlen': 1000
}


class box_detect:

    image: np.ndarray

    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig):
        """
        self.config = config

    @cached_property
    def ui_mask(self):
        return EQUIP_MASK.image

    @cached_property
    def ui_mask_stroke(self):
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        image = cv2.erode(self.ui_mask, kernel).astype('uint8')
        return image

    def load_image(self, image):
        """Method that turns image to monochrome and hide UI.

        Args:
            image: Screenshot.

        Returns:
            np.ndarray
        """
        image = rgb2gray(crop(image, DETECTING_AREA))
        image = cv2.subtract(255, cv2.bitwise_and(image, self.ui_mask))
        return image

    def find_peaks(self, image, is_horizontal, param, pad=0):
        """
        Args:
            image(np.ndarray): Processed screenshot.
            is_horizontal(bool): True if detects horizontal lines.
            param(dict): Parameters use in scipy.signal.find_peaks.
            pad(int):

        Returns:
            np.ndarray:
        """
        if is_horizontal:
            image = image.T
        if pad:
            image = np.pad(image, ((0, 0), (0, pad)),
                           mode='constant', constant_values=255)
        origin_shape = image.shape
        out = np.zeros(origin_shape[0] * origin_shape[1], dtype='uint8')
        # peaks, _ = signal.find_peaks(image.ravel(), **param)

        peaks, _ = signal.find_peaks(image.ravel(), **param)

        out[peaks] = 255
        out = out.reshape(origin_shape)
        if pad:
            out = out[:, :-pad]
        if is_horizontal:
            out = out.T
        out &= self.ui_mask_stroke
        return out

    def hough_lines(self, image, is_horizontal, threshold, theta):
        """

        Args:
            image (np.ndarray): Peaks image.
            is_horizontal (bool): True if detects horizontal lines.
            threshold (int): Threshold use in cv2.HoughLines
            theta:

        Returns:
            Lines:
        """
        lines = cv2.HoughLines(image, 1, np.pi / 180, threshold)
        if lines is None:
            return Lines(None, is_horizontal=is_horizontal, config=self.config)
        else:
            lines = lines[:, 0, :]
        if is_horizontal:
            lines = lines[(np.deg2rad(90 - theta) < lines[:, 1])
                          & (lines[:, 1] < np.deg2rad(90 + theta))]
        else:
            lines = lines[(lines[:, 1] < np.deg2rad(theta)) |
                          (np.deg2rad(180 - theta) < lines[:, 1])]
            lines = [[-rho, theta - np.pi] if rho < 0 else [rho, theta]
                     for rho, theta in lines]
        # if len(lines) > 0:
        #     return Lines(lines, is_horizontal=is_horizontal, config=self.config)
        return Lines(lines, is_horizontal=is_horizontal, config=self.config)

    def detect_lines(self, image, is_horizontal, param, threshold, theta, pad=0):
        """
        Method that wraps find_peaks and hough_lines
        """
        peaks = self.find_peaks(
            image=image, is_horizontal=is_horizontal, param=param, pad=pad)
        # self.show_array(peaks)
        lines = self.hough_lines(
            peaks, is_horizontal=is_horizontal, threshold=threshold, theta=theta)
        # self.draw(lines, Image.fromarray(peaks.astype(np.uint8), mode='L'))
        return lines

    def draw(self, lines=None, bg=None, expend=0):
        if bg is None:
            image = self.image.copy()
        else:
            image = bg.copy()
        image = Image.fromarray(image)
        if expend:
            image = ImageOps.expand(image, border=expend, fill=0)
        draw = ImageDraw.Draw(image)
        if lines is None:
            lines = self.horizontal.add(self.vertical)
        for rho, theta in zip(lines.rho, lines.theta):
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a * rho
            y0 = b * rho
            x1 = int(x0 + 10000 * (-b)) + expend
            y1 = int(y0 + 10000 * a) + expend
            x2 = int(x0 - 10000 * (-b)) + expend
            y2 = int(y0 - 10000 * a) + expend
            draw.line([x1, y1, x2, y2], 'white')

    def load(self):
        image = self.image
        image = np.array(image)

        self.image = image
        image = self.load_image(image)

        # Lines detection
        inner_h = self.detect_lines(
            image,
            is_horizontal=True,
            param=INTERNAL_LINES_FIND_PEAKS_PARAMETERS,
            threshold=self.config.INTERNAL_LINES_HOUGHLINES_THRESHOLD,
            theta=self.config.HORIZONTAL_LINES_THETA_THRESHOLD
        ).move(*DETECTING_AREA[:2])
        inner_v = self.detect_lines(
            image,
            is_horizontal=False,
            param=INTERNAL_LINES_FIND_PEAKS_PARAMETERS,
            threshold=self.config.INTERNAL_LINES_HOUGHLINES_THRESHOLD,
            theta=self.config.VERTICAL_LINES_THETA_THRESHOLD
        ).move(*DETECTING_AREA[:2])
        edge_h = self.detect_lines(
            image,
            is_horizontal=True,
            param=EDGE_LINES_FIND_PEAKS_PARAMETERS,
            threshold=self.config.EDGE_LINES_HOUGHLINES_THRESHOLD,
            theta=self.config.HORIZONTAL_LINES_THETA_THRESHOLD,
            pad=DETECTING_AREA[2] - DETECTING_AREA[0]
        ).move(*DETECTING_AREA[:2])
        edge_v = self.detect_lines(
            image,
            is_horizontal=False,
            param=EDGE_LINES_FIND_PEAKS_PARAMETERS,
            threshold=self.config.EDGE_LINES_HOUGHLINES_THRESHOLD,
            theta=self.config.VERTICAL_LINES_THETA_THRESHOLD,
            pad=DETECTING_AREA[3] - DETECTING_AREA[1]
        ).move(*DETECTING_AREA[:2])

        # Lines pre-cleansing
        horizontal = inner_h.add(edge_h).group()
        vertical = inner_v.add(edge_v).group()
        edge_h = edge_h.group()
        edge_v = edge_v.group()

        self.horizontal = horizontal
        self.vertical = vertical

        testLines = horizontal.add(vertical)
        # print(testLines)
        self.draw(testLines)

    def crop(self, area, shape=None):
        """Crop image and rescale to target shape. Eliminate the effect of perspective.

        Args:
            area (tuple): upper_left_x, upper_left_y, bottom_right_x, bottom_right_y, such as (-1, -1, 1, 1).
            shape (tuple): Output image shape, (width, height).

        Returns:
            np.ndarray: Shape (height, width, channel).
        """
        area = np.array(area)

        image = crop(self.image, area=np.rint(area).astype(int))
        if shape is not None:
            # Follow the default re-sampling filter in pillow, which is BICUBIC.
            image = cv2.resize(image, shape, interpolation=cv2.INTER_CUBIC)
        return image

    def DivideGrid(self):
        list_h = sorted([i[0] for i in self.horizontal])
        list_v = sorted([i[0] for i in self.vertical])

        tuple_h = []
        for i in range(0, len(list_h) - 1):
            if(list_h[i + 1] - list_h[i] > 100):
                tuple_h.append((list_h[i], list_h[i + 1]))

        tuple_v = []
        for i in range(0, len(list_v) - 1):
            if(list_v[i + 1] - list_v[i] > 100):
                tuple_v.append((list_v[i], list_v[i + 1]))

        self.grid = []
        for h in tuple_h:
            for v in tuple_v:
                self.grid.append((v[0], h[0], v[1], h[1]))

        # print(len(self.grid))

    def detectBoxArea(self, image, boxList={'T1': 1, 'T2': 1, 'T3': 1}):
        self.image = image
        self.load()
        self.DivideGrid()
        areaList = []
        for i in self.grid:
            if boxList['T1'] and self.Predict_Box_T1(i):
                areaList.append(i)
                continue

            if boxList['T2'] and self.Predict_Box_T2(i):
                areaList.append(i)
                continue

            if boxList['T3'] and self.Predict_Box_T3(i):
                areaList.append(i)
                continue

        return areaList

    def detectWeaponArea(self, image):
        self.image = image
        self.load()
        self.DivideGrid()

        areaList = []
        for i in self.grid:
            if not self.Predict_Weapon_Upgrade(i):
                areaList.append(i)

        return areaList


    def Predict_Weapon_Upgrade(self, area):
        
        image = self.crop(area=area)

        # logger.info(TEMPLATE_WEAPON_PLUS.match_result(image))
        return TEMPLATE_WEAPON_PLUS.match(image, similarity=0.8)

    def Predict_Box_T1(self, area):

        image = self.crop(area=area)
        return TEMPLATE_BOX_T1.match(image, similarity=0.9)

    def Predict_Box_T2(self, area):

        image = self.crop(area=area)
        return TEMPLATE_BOX_T2.match(image, similarity=0.9)

    def Predict_Box_T3(self, area):

        image = self.crop(area=area)
        return TEMPLATE_BOX_T3.match(image, similarity=0.9)

    def Predict_Box_T4(self, area):
        image = self.crop(area=area)
        return TEMPLATE_BOX_T4.match(image, similarity=0.9)

    def test(self):
        self.load()
        self.DivideGrid()
