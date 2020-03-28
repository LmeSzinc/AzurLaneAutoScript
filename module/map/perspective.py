import os
import time
import warnings

import cv2
import numpy as np
from PIL import Image, ImageOps, ImageDraw
from scipy import signal, optimize

from module.config.config import AzurLaneConfig
from module.logger import logger
from module.map.perspective_items import Points, Lines

warnings.filterwarnings("ignore")


class Perspective:
    def __init__(self, image, config):
        """
        Args:
            image: Screenshot
            config (AzurLaneConfig):
        """
        self.image = image
        self.config = config
        self.correct = True
        start_time = time.time()

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
        # horizontal = inner_h.add(edge_h).group()
        # vertical = inner_v.add(edge_v).group()
        # edge_h = edge_h.group()
        # edge_v = edge_v.group()
        horizontal = inner_h.add(edge_h).group()
        vertical = inner_v.add(edge_v).group()
        edge_h = edge_h.group().delete(inner_h)  # Experimental, reduce edge lines.
        edge_v = edge_v.group().delete(inner_v)
        self.horizontal = horizontal
        self.vertical = vertical

        # Calculate perspective
        self.crossings = self.horizontal.cross(self.vertical)
        self.vanish_point = optimize.brute(self._vanish_point_value, self.config.VANISH_POINT_RANGE)
        distance_point_x = optimize.brute(self._distant_point_value, self.config.DISTANCE_POINT_X_RANGE)[0]
        self.distant_point = np.array([distance_point_x, self.vanish_point[1]])

        # Re-generate lines. Useless after mid_cleanse function added.
        # self.horizontal = self.crossings.link(None, is_horizontal=True).group()
        # self.vertical = self.crossings.link(self.vanish_point).group()
        # self.draw(self.crossings.link(self.distant_point))
        # print(edge_h)
        # print(inner_h.group())

        # Lines cleansing
        # self.draw(edge_h)
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
            str(time_cost).ljust(5, '0'), '_' if self.lower_edge else ' ',
            len(self.horizontal), len(horizontal), len(edge_h))
                    )
        logger.info('Edges: %s%s%s    Vertical: %s (%s inner, %s edge)' % (
            '/' if self.left_edge else ' ', '_' if self.upper_edge else ' ',
            '\\' if self.right_edge else ' ', len(self.vertical), len(vertical), len(edge_v))
                    )
        if len(horizontal) - len(self.horizontal) >= 3 or len(vertical) - len(self.vertical) >= 3:
            logger.warning('Too many deleted lines')
            # self.save_error_image()

    def load_image(self, image):
        """Method that turns image to monochrome and hide UI.

        Args:
            image: Screenshot.

        Returns:
            np.ndarray
        """
        image = np.array(image.crop(self.config.DETECTING_AREA))
        image = 255 - ((np.max(image, axis=2) // 2 + np.min(image, axis=2) // 2) & self.config.UI_MASK)
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
        out &= self.config.UI_MASK
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
            lines = lines[(np.deg2rad(90 - theta) < lines[:, 1]) & (lines[:, 1] < np.deg2rad(90 + theta))]
        else:
            lines = lines[(lines[:, 1] < np.deg2rad(theta)) | (np.deg2rad(180 - theta) < lines[:, 1])]
            lines = [[-rho, theta - np.pi] if rho < 0 else [rho, theta] for rho, theta in lines]
        # if len(lines) > 0:
        #     return Lines(lines, is_horizontal=is_horizontal, config=self.config)
        return Lines(lines, is_horizontal=is_horizontal, config=self.config)

    def detect_lines(self, image, is_horizontal, param, threshold, theta, pad=0):
        """
        Method that wraps find_peaks and hough_lines
        """
        peaks = self.find_peaks(image, is_horizontal=is_horizontal, param=param, pad=pad)
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
            np.ndarray
        """
        right_distant_point = (self.vanish_point[0] * 2 - self.distant_point[0], self.distant_point[1])

        def convert_to_x(ys):
            return Points([[self.config.SCREEN_CENTER[0], y] for y in ys], config=self.config) \
                .link(right_distant_point) \
                .mid

        def convert_to_y(xs):
            return Points([[x, self.config.SCREEN_CENTER[1]] for x in xs], config=self.config) \
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
            distance = 1 / (1 + np.exp(9 / distance) / distance)
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
        coincident = Lines(np.vstack(lines), is_horizontal=False, config=self.config)
        # print(np.round(np.sort(coincident.get_x(128))).astype(int))
        coincident_point = optimize.brute(coincident_point_value, self.config.COINCIDENT_POINT_RANGE)
        # print(coincident_point, is_horizontal)

        diff = abs(coincident_point[1] - 129)
        if diff > 3:
            self.correct = False
            logger.warning('%s coincident point unexpected: %s' % (
                'Horizontal' if is_horizontal else 'Vertical',
                str(coincident_point)))
            if diff > 6:
                self.save_error_image()

        # The limits of detecting area
        if is_horizontal:
            border = Points(
                [[self.config.SCREEN_CENTER[0], self.config.DETECTING_AREA[1]],
                 [self.config.SCREEN_CENTER[0], self.config.DETECTING_AREA[3]]], config=self.config) \
                .link(right_distant_point) \
                .mid
        else:
            border = Points(
                [self.config.DETECTING_AREA[0:2], self.config.DETECTING_AREA[1:3][::-1]], config=self.config) \
                .link(self.vanish_point) \
                .mid

        left, right = border
        # print(mids)
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
        edge = edge[(edge > np.max(inner) - threshold) | (edge < np.min(inner) + threshold)]
        edge = [c for c in clean if np.any(np.abs(c - edge) < 5)]

        # Separate edges
        if len(edge) == 0:
            lower, upper = None, None
        elif len(edge) == 1:
            edge = edge[0]
            if lines.is_horizontal:
                lower, upper = (None, edge) if edge > self.config.SCREEN_CENTER[1] else (edge, None)
            else:
                lower, upper = (None, edge) if edge > self.config.SCREEN_CENTER[0] else (edge, None)
        else:
            lower, upper = edge[0], edge[-1]

        # crop mid
        if lower:
            clean = clean[clean > lower - threshold]
        if upper:
            clean = clean[clean < upper + threshold]

        # mid to lines
        if lines.is_horizontal:
            lines = Points([[self.config.SCREEN_CENTER[0], y] for y in clean], config=self.config) \
                .link(None, is_horizontal=True)
            lower = Points([self.config.SCREEN_CENTER[0], lower], config=self.config).link(None, is_horizontal=True)  \
                if lower else Lines(None, config=self.config, is_horizontal=True)
            upper = Points([self.config.SCREEN_CENTER[0], upper], config=self.config).link(None, is_horizontal=True)  \
                if upper else Lines(None, config=self.config, is_horizontal=True)
        else:
            lines = Points([[x, self.config.SCREEN_CENTER[1]] for x in clean], config=self.config) \
                .link(self.vanish_point)
            lower = Points([lower, self.config.SCREEN_CENTER[1]], config=self.config).link(self.vanish_point)  \
                if lower else Lines(None, config=self.config, is_horizontal=False)
            upper = Points([upper, self.config.SCREEN_CENTER[1]], config=self.config).link(self.vanish_point)  \
                if upper else Lines(None, config=self.config, is_horizontal=False)

        return lines, lower, upper

    def save_error_image(self):
        file = '%s.%s' % (int(time.time() * 1000), 'png')
        file = os.path.join(self.config.ERROR_LOG_FOLDER, file)
        self.image.save(file)
