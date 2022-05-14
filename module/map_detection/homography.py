import time

import numpy as np
from PIL import ImageDraw, ImageOps

from module.base.utils import *
from module.config.config import AzurLaneConfig
from module.exception import MapDetectionError
from module.logger import logger
from module.map_detection.perspective import Perspective
from module.map_detection.utils import *
from module.map_detection.utils_assets import *


class Homography:
    """
    Homography transformation

    Examples:
        hm = Homography(AzurLaneConfig('template'))
        hm.load(image)

    Examples:
        hm = Homography(AzurLaneConfig('template'))
        storage = ((8, 3), [(80.773, 281.635), (1164.829, 281.635), (-20.123, 609.332), (1259.794, 609.332)])
        hm.load_homography(storage=storage)
        hm.detect(image)

    Logs:
                   tile_center: 0.968 (good match)
        0.062s  _   edge_lines: 3 hori, 3 vert
        Edges: /_    homo_loca: ( 26,  58)
    """

    """
    Output
    """
    image: np.ndarray
    config: AzurLaneConfig
    # Four edges in bool, or has attribute __bool__
    left_edge: int
    right_edge: int
    lower_edge: int
    upper_edge: int

    """
    Private
    """
    homo_storage: tuple
    homo_data: np.ndarray
    homo_invt: np.ndarray
    homo_size: tuple
    homo_loca: np.ndarray
    homo_loaded: bool

    map_inner: np.ndarray
    _map_edge_count: tuple

    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig):
        """
        self.config = config
        self.homo_loaded = False

    @cached_property
    def ui_mask_homo_stroke(self):
        if self.config.Scheduler_Command.startswith('Opsi'):
            mask = ASSETS.ui_mask_os
        else:
            mask = ASSETS.ui_mask
        image = cv2.warpPerspective(mask, self.homo_data, self.homo_size)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        image = cv2.erode(image, kernel).astype('uint8')
        # Remove edges, perspective transform may produce aliasing
        pad = 2
        image[:pad, :] = 0
        image[-pad:, :] = 0
        image[:, :pad] = 0
        image[:, -pad:] = 0
        return image

    def load(self, image):
        """
        Args:
            image (np.ndarray): Shape (720, 1280, 3)
        """
        if not self.homo_loaded:
            self.load_homography(storage=self.config.HOMO_STORAGE, image=image)

        self.detect(image)

    def load_homography(self, storage=None, perspective=None, image=None, file=None):
        """
        Args:
            storage (tuple): ((x, y), [upper-left, upper-right, bottom-left, bottom-right])
            perspective (Perspective):
            image (np.ndarray):
            file (str): File path of image
        """
        if storage is not None:
            self.find_homography(*storage)
        elif perspective is not None:
            hori = perspective.horizontal[0].add(perspective.horizontal[-1])
            vert = perspective.vertical[0].add(perspective.vertical[-1])
            src_pts = hori.cross(vert).points
            x = len(perspective.vertical) - 1
            y = len(perspective.horizontal) - 1
            self.find_homography(size=(x, y), src_pts=src_pts)
        elif image is not None:
            perspective_ = Perspective(self.config)
            perspective_.load(image)
            self.load_homography(perspective=perspective_)
        elif file is not None:
            image_ = load_image(file)
            perspective_ = Perspective(self.config)
            perspective_.load(image_)
            self.load_homography(perspective=perspective_)
        else:
            raise MapDetectionError('No data feed to load_homography, please input at least one.')

    def find_homography(self, size, src_pts, overflow=True):
        """
        Args:
            size (tuple): (x, y)
            src_pts (list[tuple]): [upper-left, upper-right, bottom-left, bottom-right]
            overflow (bool): True if get full transformed image, false if get valid area only.
        """
        self.homo_storage = (size, [(x, y) for x, y in np.round(src_pts, 3)])
        logger.attr('homo_storage', self.homo_storage)

        # Generate perspective data
        src_pts = np.array(src_pts) - self.config.DETECTING_AREA[:2]
        dst_pts = src_pts[0] + area2corner((0, 0, *np.multiply(size, self.config.HOMO_TILE)))
        homo = cv2.getPerspectiveTransform(src_pts.astype(np.float32), dst_pts.astype(np.float32))

        # Re-generate to align image to upper-left
        area = area2corner(self.config.DETECTING_AREA) - self.config.DETECTING_AREA[:2]
        transformed = perspective_transform(area, data=homo)
        if overflow:
            transformed -= np.min(transformed, axis=0)
            size = np.ceil(np.max(transformed, axis=0)).astype(int)
        else:
            x0, y0, x1, y1, x2, y2, x3, y3 = transformed.flatten()
            inner = np.array((max(x0, x2), max(y0, y1), min(x1, x3), min(y2, y3)))
            transformed -= inner[:2]
            size = np.ceil(inner[2:] - inner[:2]).astype(int)
        homo = cv2.getPerspectiveTransform(area.astype(np.float32), transformed.astype(np.float32))

        self.homo_data = homo
        self.homo_invt = cv2.invert(homo)[1]
        self.homo_size = tuple(size.tolist())
        self.homo_loaded = True

    def detect(self, image):
        """
        Args:
            image (np.ndarray): Screenshot.

        Returns:
            bool: If success.
        """
        start_time = time.time()
        self.image = image

        # Image initialization
        image = rgb2gray(crop(image, self.config.DETECTING_AREA))

        # Perspective transform
        image_trans = cv2.warpPerspective(image, self.homo_data, self.homo_size)

        # Edge detection
        image_edge = cv2.Canny(image_trans, *self.config.HOMO_CANNY_THRESHOLD)
        image_edge = cv2.bitwise_and(image_edge, self.ui_mask_homo_stroke)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        image_edge = cv2.morphologyEx(image_edge, cv2.MORPH_CLOSE, kernel)
        # Image.fromarray(image_edge, mode='L').show()

        # Find free tile
        if self.search_tile_center(image_edge, threshold_good=self.config.HOMO_CENTER_GOOD_THRESHOLD,
                                   threshold=self.config.HOMO_CENTER_THRESHOLD):
            pass
        elif self.search_tile_corner(image_edge, threshold=self.config.HOMO_CORNER_THRESHOLD):
            pass
        elif self.search_tile_rectangle(image_edge, threshold=self.config.HOMO_RECTANGLE_THRESHOLD):
            pass
        else:
            raise MapDetectionError('Failed to find a free tile')

        self.homo_loca %= self.config.HOMO_TILE

        # Detect map edges
        self.lower_edge, self.upper_edge, self.left_edge, self.right_edge = False, False, False, False
        self._map_edge_count = (0, 0)
        if self.config.HOMO_EDGE_DETECT:
            image_edge = cv2.bitwise_and(cv2.dilate(image_edge, kernel),
                                         cv2.inRange(image_trans, *self.config.HOMO_EDGE_COLOR_RANGE))
            image_edge = cv2.bitwise_and(image_edge, self.ui_mask_homo_stroke)
            self.detect_edges(image_edge, hough_th=self.config.HOMO_EDGE_HOUGHLINES_THRESHOLD)

        # Log
        time_cost = round(time.time() - start_time, 3)
        logger.info('%ss  %s   edge_lines: %s hori, %s vert' % (
            float2str(time_cost), '_' if self.lower_edge else ' ',
            self._map_edge_count[1], self._map_edge_count[0])
                    )
        logger.info('Edges: %s%s%s   homo_loca: %s' % (
            '/' if self.left_edge else ' ', '_' if self.upper_edge else ' ', '\\' if self.right_edge else ' ',
            point2str(*self.homo_loca, length=3))
                    )

    def search_tile_center(self, image, threshold_good=0.9, threshold=0.8, encourage=1.0):
        """
        Search for the center of empty tile.
        Note: This is the main method.
        `len(res[res > 0.8])` is 3x faster than `np.sum(res > 0.8)`

        Args:
            image (np.ndarray): Monochrome image.
            threshold_good (float);
            threshold (float):
            encourage (int, float):

        Returns:
            bool: If success.
        """
        result = cv2.matchTemplate(image, ASSETS.tile_center_image, cv2.TM_CCOEFF_NORMED)
        _, similarity, _, loca = cv2.minMaxLoc(result)
        if similarity > threshold_good:
            self.homo_loca = np.array(loca) - self.config.HOMO_CENTER_OFFSET
            self.map_inner = np.array(loca)
            message = 'good match'
        elif similarity > threshold:
            location = np.argwhere(result > threshold)[:, ::-1]
            self.homo_loca = fit_points(
                location, mod=self.config.HOMO_TILE, encourage=encourage) - self.config.HOMO_CENTER_OFFSET
            self.map_inner = get_map_inner(location)
            message = f'{len(location)} matches'
        else:
            message = 'bad match'

        # print(self.homo_loca % self.config.HOMO_TILE)
        logger.attr_align('tile_center', f'{float2str(similarity)} ({message})')
        return message != 'bad match'

    def search_tile_corner(self, image, threshold=0.8, encourage=1.0):
        """
        Search for the corner of empty tile.
        This is a fallback method, almost no need.
        Note: This method has a difference in 0.5 ~ 1.0 pixel.

        Args:
            image (np.ndarray): Monochrome image.
            threshold (float):
            encourage (int, float):

        Returns:
            bool: If success.
        """
        similarity = 0
        location = np.array([])
        for index in range(4):
            template = ASSETS.tile_corner_image_list[index]
            result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            similarity = max(similarity, np.max(result))
            loca = np.argwhere(result > threshold)[:, ::-1] - self.config.HOMO_CORNER_OFFSET_LIST[index]
            location = np.append(location, loca, axis=0) if len(location) else loca

        if similarity > threshold:
            self.homo_loca = fit_points(
                location, mod=self.config.HOMO_TILE, encourage=encourage) - self.config.HOMO_CENTER_OFFSET
            self.map_inner = get_map_inner(location)
            message = f'{len(location)} matches'
        else:
            message = 'bad match'

        # print(self.homo_loca % self.config.HOMO_TILE)
        logger.attr_align('tile_corner', f'{float2str(similarity)} ({message})')
        return message != 'bad match'

    def search_tile_rectangle(self, image, threshold=10, encourage=5.1, close_kernel=(5, 10, 15, 20, 25)):
        """
        Search for the corner of empty tile.
        This is a fallback method for fallback method, almost almost no need.
        Note: This method may have a difference in about 2 pixels.

        Args:
            image (np.ndarray): Monochrome image.
            threshold (int): Number of rectangles.
            encourage (int, float):
            close_kernel (tuple[int]): Kernel size use in morphology close

        Returns:
            bool: If success.
        """
        location = np.array([])
        for kernel in close_kernel:
            # Re-creating closed image
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel, kernel))
            image_closed = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
            # Find rectangles
            contours, _ = cv2.findContours(image_closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            rectangle = np.array([cv2.boundingRect(cv2.convexHull(cont).astype(np.float32)) for cont in contours])

            try:
                # Filter out correct rectangles
                rectangle = rectangle[(rectangle[:, 2] > 100) & (rectangle[:, 3] > 100)]
                shape = rectangle[:, 2:]
                diff = np.abs(shape - np.round(shape / self.config.HOMO_TILE) * self.config.HOMO_TILE)
                rectangle = rectangle[np.all(diff < encourage, axis=1)]
                location = np.append(location, rectangle[:, :2], axis=0) if len(location) else rectangle[:, :2]
            except IndexError:
                location = []

        if len(location) > threshold:
            self.homo_loca = fit_points(location, mod=self.config.HOMO_TILE, encourage=encourage)
            self.map_inner = get_map_inner(location)
            message = 'good match'
        else:
            message = 'bad match'

        # print(self.homo_loca % self.config.HOMO_TILE)
        logger.attr_align('tile_rectangle', f'{len(location)} rectangles ({message})')
        return message != 'bad match'

    def detect_edges(self, image, hough_th=120, theta_th=0.005, edge_th=9):
        """
        Detect map edges

        Args:
            image (np.ndarray): Monochrome image.
            hough_th (int): cv2.HoughLines threshold.
            theta_th (float): Lines theta threshold, in degree.
            edge_th (int): Edge threshold, in pixel.
        """
        lines = cv2.HoughLines(image, 1, np.pi / 180, hough_th)
        if lines is None:
            self.lower_edge, self.upper_edge = separate_edges([], inner=self.map_inner[1])
            self.left_edge, self.right_edge = separate_edges([], inner=self.map_inner[0])
            self._map_edge_count = (0, 0)
            return None

        lines = lines[:, 0, :]
        rho, theta = lines[:, 0], lines[:, 1]
        area = self.config.DETECTING_AREA
        area = area2corner([0, 0, *np.subtract(area[2:], area[:2])])
        area = np.mean(area.reshape((2, 2, 2)), axis=0)
        area = perspective_transform(area, self.homo_data)
        mid_left, _, mid_right, _ = area.flatten()

        hori = lines[(np.deg2rad(90 - theta_th) < theta) & (theta < np.deg2rad(90 + theta_th))]
        hori = Lines(hori, is_horizontal=True).group()
        vert = lines[(theta < np.deg2rad(theta_th)) | (np.deg2rad(180 - theta_th) < theta)]
        vert = [[-rho, theta - np.pi] if rho < 0 else [rho, theta] for rho, theta in vert]
        vert = [[rho, theta] for rho, theta in vert if mid_left < rho < mid_right]
        vert = Lines(vert, is_horizontal=False).group()

        self._map_edge_count = (len(vert), len(hori))

        if hori:
            hori = hori.rho
            diff = (hori - self.homo_loca[1]) % self.config.HOMO_TILE[1]
            hori = hori[(diff < edge_th) | (diff > self.config.HOMO_TILE[1] - edge_th)]
        if vert:
            vert = vert.rho
            diff = (vert - self.homo_loca[0]) % self.config.HOMO_TILE[0]
            vert = vert[(diff < edge_th) | (diff > self.config.HOMO_TILE[0] - edge_th)]

        self.lower_edge, self.upper_edge = separate_edges(hori, inner=self.map_inner[1])
        self.left_edge, self.right_edge = separate_edges(vert, inner=self.map_inner[0])

    def generate(self):
        """
        Yields (tuple): ((x, y), [upper-left, upper-right, bottom-left, bottom-right])
        """
        area = [
            self.left_edge - 5 if self.left_edge else 0,
            self.lower_edge - 5 if self.lower_edge else 0,
            self.right_edge + 5 if self.right_edge else self.homo_size[0],
            self.upper_edge + 5 if self.upper_edge else self.homo_size[1]
        ]
        x = np.arange(-25, 25) * self.config.HOMO_TILE[0] + self.homo_loca[0]
        x = x[(x > area[0]) & (x < area[2])]
        y = np.arange(-25, 25) * self.config.HOMO_TILE[1] + self.homo_loca[1]
        y = y[(y > area[1]) & (y < area[3])]

        shape = (len(x), len(y))
        points = np.array(np.meshgrid(x, y)).reshape((2, -1)).T
        points = perspective_transform(points, data=self.homo_invt) + self.config.DETECTING_AREA[:2]
        for data in points_to_area_generator(points.reshape(*shape[::-1], 2), shape=shape):
            yield data

    def to_perspective(self):
        """
        Returns:
            (Lines, Lines): Horizontal lines, vertical lines.
        """
        grids = {}
        for loca, points in self.generate():
            grids[loca] = points
        shape = np.max(list(grids.keys()), axis=0)

        hori = Points([640, grids[(0, 0)][1, 1]]).link(None, is_horizontal=True)
        for y in range(shape[1] + 1):
            hori = hori.add(Points([640, grids[(0, y)][3, 1]]).link(None, is_horizontal=True))
        vert = Points(grids[(0, 0)][1]).link(grids[(0, shape[1])][3])
        for x in range(shape[0] + 1):
            vert = vert.add(Points(grids[(x, 0)][1]).link(grids[(x, shape[1])][3]))
        return hori, vert

    def draw(self, lines=None, bg=None, expend=0):
        if lines is None:
            hori, vert = self.to_perspective()
            lines = hori.add(vert)
        if bg is None:
            image = self.image.copy()
        else:
            image = bg.copy()
        image = Image.fromarray(image)
        if expend:
            image = ImageOps.expand(image, border=expend, fill=0)
        draw = ImageDraw.Draw(image)
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
