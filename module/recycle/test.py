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
from module.map_detection.perspective import Perspective
from module.map_detection.utils import *
from module.map_detection.grid_predictor import GridPredictor
from module.template.assets import *

from module.ocr.ocr import Ocr

DETECTING_AREA = (0, 0, 1280, 720)

UI_MASK = Mask(file='./assets/mask/MASK_EQUIPMENT.png')

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
# Parameters for cv2.HoughLines
INTERNAL_LINES_HOUGHLINES_THRESHOLD = 75
EDGE_LINES_HOUGHLINES_THRESHOLD = 75
# Parameters for lines pre-cleansing
HORIZONTAL_LINES_THETA_THRESHOLD = 0.005
VERTICAL_LINES_THETA_THRESHOLD = 18


class test:

    image: np.ndarray

    def __init__(self, config, file):
        """
        Args:
            config (AzurLaneConfig):
        """
        self.config = config
        self.file = file

    @cached_property
    def ui_mask(self):
        return UI_MASK.image

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

        image.show()

    def load(self):
        file = self.file
        image = np.array(Image.open(file).convert('RGB'))

        self.image = image
        image = self.load_image(image)

        # Lines detection
        inner_h = self.detect_lines(
            image,
            is_horizontal=True,
            param=INTERNAL_LINES_FIND_PEAKS_PARAMETERS,
            threshold=INTERNAL_LINES_HOUGHLINES_THRESHOLD,
            theta=HORIZONTAL_LINES_THETA_THRESHOLD
        ).move(*DETECTING_AREA[:2])
        inner_v = self.detect_lines(
            image,
            is_horizontal=False,
            param=INTERNAL_LINES_FIND_PEAKS_PARAMETERS,
            threshold=INTERNAL_LINES_HOUGHLINES_THRESHOLD,
            theta=VERTICAL_LINES_THETA_THRESHOLD
        ).move(*DETECTING_AREA[:2])
        edge_h = self.detect_lines(
            image,
            is_horizontal=True,
            param=EDGE_LINES_FIND_PEAKS_PARAMETERS,
            threshold=EDGE_LINES_HOUGHLINES_THRESHOLD,
            theta=HORIZONTAL_LINES_THETA_THRESHOLD,
            pad=DETECTING_AREA[2] - DETECTING_AREA[0]
        ).move(*DETECTING_AREA[:2])
        edge_v = self.detect_lines(
            image,
            is_horizontal=False,
            param=EDGE_LINES_FIND_PEAKS_PARAMETERS,
            threshold=EDGE_LINES_HOUGHLINES_THRESHOLD,
            theta=VERTICAL_LINES_THETA_THRESHOLD,
            pad=DETECTING_AREA[3] - DETECTING_AREA[1]
        ).move(*DETECTING_AREA[:2])

        # self.draw(edge_h)
        # self.draw(edge_v)
        # self.draw(inner_h)
        # self.draw(inner_v)

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

    def template_crop(self, area, shape=None):
        area = np.array(area)

        center = np.array([(area[0]+area[2])/2, (area[1]+area[3])/2])
        area = np.array([center[0] - 31, center[1] - 7, center[0] - 9, center[1] + 35])

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

        ocr = Ocr(self.grid[14])
        print(ocr.ocr(Image.fromarray(self.crop(area=self.grid[14]))))

        for i in self.grid:
            # Image.fromarray(self.template_crop(area=i)).show()
            if self.Predict_Box_T1(i):
                Image.fromarray(self.crop(area=i)).show()
                print(1)

            if self.Predict_Box_T2(i):
                Image.fromarray(self.crop(area=i)).show()
                print(2)

            if self.Predict_Box_T3(i):
                Image.fromarray(self.crop(area=i)).show()
                print(3)
            
            if self.Predict_Box_T4(i):
                Image.fromarray(self.crop(area=i)).show()
                print(4)

    def Predict(self):
        pass

    def Predict_Box_T1(self, area):
        
        image = self.crop(area=area)
        # print(TEMPLATE_BOX_T1.image.shape)
        # print(TEMPLATE_BOX_T1.match_result(image))
        return TEMPLATE_BOX_T1.match(image, similarity=0.9)

    def Predict_Box_T2(self, area):

        image = self.crop(area=area)
        # print(TEMPLATE_BOX_T2.image.shape)
        # print(TEMPLATE_BOX_T2.match_result(image))
        return TEMPLATE_BOX_T2.match(image, similarity=0.9)

    def Predict_Box_T3(self, area):

        image = self.crop(area=area)
        # print(TEMPLATE_BOX_T3.image.shape)
        # print(TEMPLATE_BOX_T3.match_result(image))
        return TEMPLATE_BOX_T3.match(image, similarity=0.9)

    def Predict_Box_T4(self, area):

        image = self.crop(area=area)
        # print(TEMPLATE_BOX_T4.image.shape)
        # print(TEMPLATE_BOX_T4.match_result(image))
        return TEMPLATE_BOX_T4.match(image, similarity=0.9)
    
    

    def test(self):
        self.load()
        self.DivideGrid()


if __name__ == "__main__":
    t = test(AzurLaneConfig, r"module\recycle\test3.png")

    t.test()

