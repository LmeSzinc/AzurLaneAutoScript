import time
import warnings

import numpy as np
from PIL import Image, ImageDraw, ImageOps
from scipy import signal

from module.base.utils import *
from module.config.config import AzurLaneConfig
from module.exception import MapDetectionError
from module.logger import logger
from module.map_detection.utils import *
from module.map_detection.utils_assets import *

warnings.filterwarnings("ignore")


class Perspective:
    """
    Perspective detection

    Examples:
        persp = Perspective(AzurLaneConfig('template'))
        persp.load(image)

    Logs:
                  vanish_point: (  646, -1736)
                 distant_point: (-2321, -1736)
        0.155s  _   Horizontal: 5 (7 inner, 3 edge)
        Edges: /_     Vertical: 9 (10 inner, 3 edge)
    """

    """
    Output
    """
    image: np.ndarray
    config: AzurLaneConfig
    # Four edges in bool, or has attribute __bool__
    left_edge: Lines
    right_edge: Lines
    lower_edge: Lines
    upper_edge: Lines

    """
    Private
    """
    horizontal: Lines
    vertical: Lines
    crossings: Points
    vanish_point: tuple
    distant_point: tuple
    map_inner: np.ndarray

    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig):
        """
        self.config = config

    def load(self, image):
        """
        Args:
            image (np.ndarray): Shape (720, 1280, 3)
        """
        start_time = time.time()
        self.image = image

        # Image initialisation
        image = self.load_image(image)

        # Lines detection
        inner_h = self.detect_lines(
            image,
            is_horizontal=True,
            param=self.config.INTERNAL_LINES_FIND_PEAKS_PARAMETERS,
            threshold=self.config.INTERNAL_LINES_HOUGHLINES_THRESHOLD,
            theta=self.config.HORIZONTAL_LINES_THETA_THRESHOLD
        ).move(*self.config.DETECTING_AREA[:2])
        inner_v = self.detect_lines(
            image,
            is_horizontal=False,
            param=self.config.INTERNAL_LINES_FIND_PEAKS_PARAMETERS,
            threshold=self.config.INTERNAL_LINES_HOUGHLINES_THRESHOLD,
            theta=self.config.VERTICAL_LINES_THETA_THRESHOLD
        ).move(*self.config.DETECTING_AREA[:2])
        edge_h = self.detect_lines(
            image,
            is_horizontal=True,
            param=self.config.EDGE_LINES_FIND_PEAKS_PARAMETERS,
            threshold=self.config.EDGE_LINES_HOUGHLINES_THRESHOLD,
            theta=self.config.HORIZONTAL_LINES_THETA_THRESHOLD,
            pad=self.config.DETECTING_AREA[2] - self.config.DETECTING_AREA[0]
        ).move(*self.config.DETECTING_AREA[:2])
        edge_v = self.detect_lines(
            image,
            is_horizontal=False,
            param=self.config.EDGE_LINES_FIND_PEAKS_PARAMETERS,
            threshold=self.config.EDGE_LINES_HOUGHLINES_THRESHOLD,
            theta=self.config.VERTICAL_LINES_THETA_THRESHOLD,
            pad=self.config.DETECTING_AREA[3] - self.config.DETECTING_AREA[1]
        ).move(*self.config.DETECTING_AREA[:2])

        # Lines pre-cleansing
        horizontal = inner_h.add(edge_h).group()
        vertical = inner_v.add(edge_v).group()
        edge_h = edge_h.group()
        edge_v = edge_v.group()
        if not self.config.TRUST_EDGE_LINES:
            # Experimental, reduce edge lines.
            edge_h = edge_h.delete(inner_h, threshold=self.config.TRUST_EDGE_LINES_THRESHOLD)
            edge_v = edge_v.delete(inner_v, threshold=self.config.TRUST_EDGE_LINES_THRESHOLD)
        self.horizontal = horizontal
        self.vertical = vertical
        if not self.horizontal:
            raise MapDetectionError('No horizontal line detected')
        if not self.vertical:
            raise MapDetectionError('No vertical line detected')

        # Calculate perspective
        self.crossings = self.horizontal.cross(self.vertical)
        self.vanish_point = optimize.brute(self._vanish_point_value, self.config.VANISH_POINT_RANGE)
        distance_point_x = optimize.brute(self._distant_point_value, self.config.DISTANCE_POINT_X_RANGE)[0]
        self.distant_point = (distance_point_x, self.vanish_point[1])
        logger.attr_align('vanish_point', point2str(*self.vanish_point, length=5))
        logger.attr_align('distant_point', point2str(*self.distant_point, length=5))
        if np.linalg.norm(np.subtract(self.vanish_point, self.distant_point)) < 10:
            raise MapDetectionError('Vanish point and distant point too close')

        # Re-generate lines. Useless after mid_cleanse function added.
        # self.horizontal = self.crossings.link(None, is_horizontal=True).group()
        # self.vertical = self.crossings.link(self.vanish_point).group()
        # self.draw(self.crossings.link(self.distant_point))
        # print(edge_h)
        # print(inner_h.group())

        # Lines cleansing
        # self.draw()
        self.map_inner = get_map_inner(self.crossings.points)
        self.horizontal, self.lower_edge, self.upper_edge = self.line_cleanse(
            self.horizontal, inner=inner_h.group(), edge=edge_h)
        self.vertical, self.left_edge, self.right_edge = self.line_cleanse(
            self.vertical, inner=inner_v.group(), edge=edge_v)

        # self.draw()
        # print(self.horizontal)
        # print(self.lower_edge, self.upper_edge)
        # print(self.vertical)
        # print(self.left_edge, self.right_edge)

        # Log
        time_cost = round(time.time() - start_time, 3)
        logger.info('%ss  %s   Horizontal: %s (%s inner, %s edge)' % (
            float2str(time_cost), '_' if self.lower_edge else ' ',
            len(self.horizontal), len(horizontal), len(edge_h))
                    )
        logger.info('Edges: %s%s%s    Vertical: %s (%s inner, %s edge)' % (
            '/' if self.left_edge else ' ', '_' if self.upper_edge else ' ',
            '\\' if self.right_edge else ' ', len(self.vertical), len(vertical), len(edge_v))
                    )

    def load_image(self, image):
        """Method that turns image to monochrome and hide UI.

        Args:
            image: Screenshot.

        Returns:
            np.ndarray
        """
        image = rgb2gray(crop(image, self.config.DETECTING_AREA))
        image = cv2.subtract(255, cv2.bitwise_and(image, ASSETS.ui_mask))
        return image

    @staticmethod
    def find_peaks(image, is_horizontal, param, pad=0, mask=None):
        """
        Args:
            image(np.ndarray): Processed screenshot.
            is_horizontal(bool): True if detects horizontal lines.
            param(dict): Parameters use in scipy.signal.find_peaks.
            pad(int):
            mask(np.ndarray, None):

        Returns:
            np.ndarray:
        """
        if is_horizontal:
            image = image.T
        if pad:
            image = np.pad(image, ((0, 0), (0, pad)), mode='constant', constant_values=255)
        origin_shape = image.shape
        out = np.zeros(origin_shape[0] * origin_shape[1], dtype='uint8')
        peaks, _ = signal.find_peaks(image.ravel(), **param)
        out[peaks] = 255
        out = out.reshape(origin_shape)
        if pad:
            out = out[:, :-pad]
        if is_horizontal:
            out = out.T
        if mask is not None:
            out &= mask
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
            return Lines(None, is_horizontal=is_horizontal)
        else:
            lines = lines[:, 0, :]
        if is_horizontal:
            lines = lines[(np.deg2rad(90 - theta) < lines[:, 1]) & (lines[:, 1] < np.deg2rad(90 + theta))]
        else:
            lines = lines[(lines[:, 1] < np.deg2rad(theta)) | (np.deg2rad(180 - theta) < lines[:, 1])]
            lines = [[-rho, theta - np.pi] if rho < 0 else [rho, theta] for rho, theta in lines]
        # if len(lines) > 0:
        #     return Lines(lines, is_horizontal=is_horizontal)
        return Lines(lines, is_horizontal=is_horizontal)

    def detect_lines(self, image, is_horizontal, param, threshold, theta, pad=0):
        """
        Method that wraps find_peaks and hough_lines
        """
        peaks = self.find_peaks(image, is_horizontal=is_horizontal, param=param, pad=pad, mask=ASSETS.ui_mask_stroke)
        # self.show_array(peaks)
        lines = self.hough_lines(peaks, is_horizontal=is_horizontal, threshold=threshold, theta=theta)
        # self.draw(lines, Image.fromarray(peaks.astype(np.uint8), mode='L'))
        return lines

    @staticmethod
    def show_array(arr):
        image = Image.fromarray(arr.astype(np.uint8), mode='L')
        image.show()

    def draw(self, lines=None, bg=None, expend=0):
        if bg is None:
            image = self.image.copy()
        else:
            image = bg.copy()
        if isinstance(image, np.ndarray):
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
        # image.save('123.png')

    def _vanish_point_value(self, point):
        """Value that measures how close a point to the perspective vanish point. The smaller the better.
        Use log10 to encourage a group of coincident lines and discourage wrong lines.

        Args:
            point(np.ndarray): np.array([x, y])

        Returns:
            float: value.
        """
        # Add 0.001 to avoid log10(0).
        distance = np.sum(np.log10(np.abs(self.vertical.distance_to_point(point)) + 0.001))
        return distance

    def _distant_point_value(self, x):
        """Value that measures how close a point to the perspective distant point. The smaller the better.
        Use log10 to encourage a group of coincident lines and discourage wrong lines.

        Args:
            x(np.ndarray): np.array([x])

        Returns:
            float: value
        """
        links = self.crossings.link((x[0], self.vanish_point[1]))
        mid = np.sort(links.mid)
        distance = np.sum(np.log10(np.diff(mid) + 0.001))  # Add 0.001 to avoid log10(0).
        return distance

    def mid_cleanse(self, mids, is_horizontal, threshold=3):
        """
        Args:
            mids(np.ndarray): Lines.mid
            is_horizontal(bool): True if detects horizontal lines.
            threshold(int):

        Returns:
            np.ndarray: All correct lines.mid in DETECTING_AREA. Such as:
            [ 147.52489312  276.64750191  405.77011071  534.89271951  664.0153283
            793.1379371   922.2605459  1051.38315469 1180.50576349 1309.62837229]
        """
        right_distant_point = (self.vanish_point[0] * 2 - self.distant_point[0], self.distant_point[1])
        encourage = self.config.COINCIDENT_POINT_ENCOURAGE_DISTANCE ** 2

        def convert_to_x(ys):
            return Points([[self.config.SCREEN_CENTER[0], y] for y in ys]) \
                .link(right_distant_point) \
                .mid

        def convert_to_y(xs):
            return Points([[x, self.config.SCREEN_CENTER[1]] for x in xs]) \
                .link(right_distant_point) \
                .get_y(x=self.config.SCREEN_CENTER[0])

        def coincident_point_value(point):
            """Value that measures how close a point to the coincident point. The smaller the better.
            Coincident point may be many.
            Use an activation function to encourage a group of coincident lines and ignore wrong lines.
            """
            x, y = point
            # Do not use:
            # distance = coincident.distance_to_point(point)
            distance = np.abs(x - coincident.get_x(y))
            # print((distance * 1).astype(int).reshape(len(mids), np.diff(self.config.ERROR_LINES_TOLERANCE)[0]+1))

            # Activation function
            # distance = 1 / (1 + np.exp(16 / distance - distance))
            distance = 1 / (1 + np.exp(encourage / distance) / distance)
            distance = np.sum(distance)
            return distance

        if is_horizontal:
            mids = convert_to_x(mids)

        # Drawing lines
        lines = []
        for index, mid in enumerate(mids):
            for n in range(self.config.ERROR_LINES_TOLERANCE[0], self.config.ERROR_LINES_TOLERANCE[1] + 1):
                theta = np.arctan(index + n)
                rho = mid * np.cos(theta)
                lines.append([rho, theta])
        # Fitting mid
        coincident = Lines(np.vstack(lines), is_horizontal=False)
        # print(np.round(np.sort(coincident.get_x(128))).astype(int))
        mid_diff_range = self.config.MID_DIFF_RANGE_H if is_horizontal else self.config.MID_DIFF_RANGE_V
        coincident_point_range = ((-abs(self.config.ERROR_LINES_TOLERANCE[0]) * mid_diff_range[1], 200), mid_diff_range)
        coincident_point = optimize.brute(coincident_point_value, coincident_point_range)
        # print(coincident_point, is_horizontal)

        diff = np.max([mid_diff_range[0] - coincident_point[1], coincident_point[1] - mid_diff_range[1]])
        if diff > 0:
            logger.info('%s coincident point unexpected: %s' % (
                'Horizontal' if is_horizontal else 'Vertical',
                str(coincident_point)))

        # The limits of detecting area
        if is_horizontal:
            border = Points(
                [[self.config.SCREEN_CENTER[0], self.config.DETECTING_AREA[1]],
                 [self.config.SCREEN_CENTER[0], self.config.DETECTING_AREA[3]]]) \
                .link(right_distant_point) \
                .mid
        else:
            border = Points(
                [self.config.DETECTING_AREA[0:2], self.config.DETECTING_AREA[1:3][::-1]]) \
                .link(self.vanish_point) \
                .mid

        left, right = border
        # print(mids)
        # print(np.diff(mids))
        # Filling mid
        mids = np.arange(-25, 25) * coincident_point[1] + coincident_point[0]
        mids = mids[(mids > left - threshold) & (mids < right + threshold)]
        # print(mids)
        if is_horizontal:
            mids = convert_to_y(mids)

        return mids

    def line_cleanse(self, lines, inner, edge, threshold=3):
        origin = lines.mid
        clean = self.mid_cleanse(origin, is_horizontal=lines.is_horizontal, threshold=threshold)

        # Cleansing edge
        edge = edge.mid
        inner = inner.mid
        inner_clean = [l for l in inner if np.any(np.abs(l - clean) < 5)]  # Use correct inner to delete wrong edge.
        if len(inner_clean) > 0:
            edge = edge[(edge > np.max(inner_clean) - threshold) | (edge < np.min(inner_clean) + threshold)]
        edge = [c for c in clean if np.any(np.abs(c - edge) < 5)]

        # Separate edges
        lower, upper = separate_edges(edge, inner=self.map_inner[1] if lines.is_horizontal else self.map_inner[0])

        # crop mid
        if lower:
            clean = clean[clean > lower - threshold]
        if upper:
            clean = clean[clean < upper + threshold]

        # mid to lines
        if lines.is_horizontal:
            lines = Points([[self.config.SCREEN_CENTER[0], y] for y in clean]) \
                .link(None, is_horizontal=True)
            lower = Points([self.config.SCREEN_CENTER[0], lower]).link(None, is_horizontal=True) \
                if lower else Lines(None, is_horizontal=True)
            upper = Points([self.config.SCREEN_CENTER[0], upper]).link(None, is_horizontal=True) \
                if upper else Lines(None, is_horizontal=True)
        else:
            lines = Points([[x, self.config.SCREEN_CENTER[1]] for x in clean]) \
                .link(self.vanish_point)
            lower = Points([lower, self.config.SCREEN_CENTER[1]]).link(self.vanish_point) \
                if lower else Lines(None, is_horizontal=False)
            upper = Points([upper, self.config.SCREEN_CENTER[1]]).link(self.vanish_point) \
                if upper else Lines(None, is_horizontal=False)

        return lines, lower, upper

    def generate(self):
        """
        Yields (tuple): ((x, y), [upper-left, upper-right, bottom-left, bottom-right])
        """
        points = self.horizontal.cross(self.vertical).points
        for data in points_to_area_generator(points, shape=(len(self.vertical), len(self.horizontal))):
            yield data
