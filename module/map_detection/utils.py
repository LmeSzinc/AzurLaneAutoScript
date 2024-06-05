import numpy as np
from scipy import optimize

from module.base.utils import area_pad


class Points:
    def __init__(self, points):
        if points is None or len(points) == 0:
            self._bool = False
            self.points = None
        else:
            self._bool = True
            self.points = np.array(points)
            if len(self.points.shape) == 1:
                self.points = np.array([self.points])
            self.x, self.y = self.points.T

    def __str__(self):
        return str(self.points)

    __repr__ = __str__

    def __iter__(self):
        return iter(self.points)

    def __getitem__(self, item):
        return self.points[item]

    def __len__(self):
        if self:
            return len(self.points)
        else:
            return 0

    def __bool__(self):
        return self._bool

    def link(self, point, is_horizontal=False):
        if is_horizontal:
            lines = [[y, np.pi / 2] for y in self.y]
            return Lines(lines, is_horizontal=True)
        else:
            x, y = point
            theta = -np.arctan((self.x - x) / (self.y - y))
            rho = self.x * np.cos(theta) + self.y * np.sin(theta)
            lines = np.array([rho, theta]).T
            return Lines(lines, is_horizontal=False)

    def mean(self):
        if not self:
            return None

        return np.round(np.mean(self.points, axis=0)).astype(int)

    def group(self, threshold=3):
        if not self:
            return np.array([])
        groups = []
        points = self.points
        if len(points) == 1:
            return np.array([points[0]])

        while len(points):
            p0, p1 = points[0], points[1:]
            distance = np.sum(np.abs(p1 - p0), axis=1)
            new = Points(np.append(p1[distance <= threshold], [p0], axis=0)).mean().tolist()
            groups.append(new)
            points = p1[distance > threshold]

        return np.array(groups)


class Lines:
    MID_Y = 360

    def __init__(self, lines, is_horizontal):
        if lines is None or len(lines) == 0:
            self._bool = False
            self.lines = None
        else:
            self._bool = True
            self.lines = np.array(lines)
            if len(self.lines.shape) == 1:
                self.lines = np.array([self.lines])
            self.rho, self.theta = self.lines.T
        self.is_horizontal = is_horizontal

    def __str__(self):
        return str(self.lines)

    __repr__ = __str__

    def __iter__(self):
        return iter(self.lines)

    def __getitem__(self, item):
        return Lines(self.lines[item], is_horizontal=self.is_horizontal)

    def __len__(self):
        if self:
            return len(self.lines)
        else:
            return 0

    def __bool__(self):
        return self._bool

    @property
    def sin(self):
        return np.sin(self.theta)

    @property
    def cos(self):
        return np.cos(self.theta)

    @property
    def mean(self):
        if not self:
            return None
        if self.is_horizontal:
            return np.mean(self.lines, axis=0)
        else:
            x = np.mean(self.mid)
            theta = np.mean(self.theta)
            rho = x * np.cos(theta) + self.MID_Y * np.sin(theta)
            return np.array((rho, theta))

    @property
    def mid(self):
        if not self:
            return np.array([])
        if self.is_horizontal:
            return self.rho
        else:
            return (self.rho - self.MID_Y * self.sin) / self.cos

    def get_x(self, y):
        return (self.rho - y * self.sin) / self.cos

    def get_y(self, x):
        return (self.rho - x * self.cos) / self.sin

    def add(self, other):
        if not other:
            return self
        if not self:
            return other
        lines = np.append(self.lines, other.lines, axis=0)
        return Lines(lines, is_horizontal=self.is_horizontal)

    def move(self, x, y):
        if not self:
            return self
        if self.is_horizontal:
            self.lines[:, 0] += y
        else:
            self.lines[:, 0] += x * self.cos + y * self.sin
        return Lines(self.lines, is_horizontal=self.is_horizontal)

    def sort(self):
        if not self:
            return self
        lines = self.lines[np.argsort(self.mid)]
        return Lines(lines, is_horizontal=self.is_horizontal)

    def group(self, threshold=3):
        if not self:
            return self
        lines = self.sort()
        prev = 0
        regrouped = []
        group = []
        for mid, line in zip(lines.mid, lines.lines):
            line = line.tolist()
            if mid - prev > threshold:
                if len(regrouped) == 0:
                    if len(group) != 0:
                        regrouped = [group]
                else:
                    regrouped += [group]
                group = [line]
            else:
                group.append(line)
            prev = mid
        regrouped += [group]
        regrouped = np.vstack([Lines(r, is_horizontal=self.is_horizontal).mean for r in regrouped])
        return Lines(regrouped, is_horizontal=self.is_horizontal)

    def distance_to_point(self, point):
        x, y = point
        return self.rho - x * self.cos - y * self.sin

    @staticmethod
    def cross_two_lines(lines1, lines2):
        for rho1, sin1, cos1 in zip(lines1.rho, lines1.sin, lines1.cos):
            for rho2, sin2, cos2 in zip(lines2.rho, lines2.sin, lines2.cos):
                a = np.array([[cos1, sin1], [cos2, sin2]])
                b = np.array([rho1, rho2])
                yield np.linalg.solve(a, b)

    def cross(self, other):
        points = np.vstack(self.cross_two_lines(self, other))
        points = Points(points)
        return points

    def delete(self, other, threshold=3):
        if not self:
            return self

        other_mid = other.mid
        lines = []
        for mid, line in zip(self.mid, self.lines):
            if np.any(np.abs(other_mid - mid) < threshold):
                continue
            lines.append(line)

        return Lines(lines, is_horizontal=self.is_horizontal)


def area2corner(area):
    """
    Args:
        area: (x1, y1, x2, y2)

    Returns:
        np.ndarray: [upper-left, upper-right, bottom-left, bottom-right]
    """
    return np.array([[area[0], area[1]], [area[2], area[1]], [area[0], area[3]], [area[2], area[3]]])


def corner2area(corner):
    """
    Args:
        corner: [upper-left, upper-right, bottom-left, bottom-right]

    Returns:
        np.ndarray: (x1, y1, x2, y2)
    """
    x, y = np.array(corner).T
    return np.rint([np.min(x), np.min(y), np.max(x), np.max(y)]).astype(int)


def corner2inner(corner):
    """
    The largest rectangle inscribed in trapezoid.

    Args:
        corner: ((x0, y0), (x1, y1), (x2, y2), (x3, y3))

    Returns:
        tuple[int]: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
    """
    x0, y0, x1, y1, x2, y2, x3, y3 = np.array(corner).flatten()
    area = tuple(np.rint((max(x0, x2), max(y0, y1), min(x1, x3), min(y2, y3))).astype(int))
    return area


def corner2outer(corner):
    """
    The smallest rectangle circumscribed by the trapezoid.

    Args:
        corner: ((x0, y0), (x1, y1), (x2, y2), (x3, y3))

    Returns:
        tuple[int]: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
    """
    x0, y0, x1, y1, x2, y2, x3, y3 = np.array(corner).flatten()
    area = tuple(np.rint((min(x0, x2), min(y0, y1), max(x1, x3), max(y2, y3))).astype(int))
    return area


def trapezoid2area(corner, pad=0):
    """
    Convert corners of a trapezoid to area.

    Args:
        corner: ((x0, y0), (x1, y1), (x2, y2), (x3, y3))
        pad (int):
            Positive value for inscribed area.
            Negative value and 0 for circumscribed area.

    Returns:
        tuple[int]: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
    """
    if pad > 0:
        return area_pad(corner2inner(corner), pad=pad)
    elif pad < 0:
        return area_pad(corner2outer(corner), pad=pad)
    else:
        return area_pad(corner2area(corner), pad=pad)


def points_to_area_generator(points, shape):
    """
    Args:
        points (np.ndarray): N x 2 array.
        shape (tuple): (x, y).

    Yields:
        tuple, np.ndarray: (x, y), [upper-left, upper-right, bottom-left, bottom-right]
    """
    points = points.reshape(*shape[::-1], 2)
    for y in range(shape[1] - 1):
        for x in range(shape[0] - 1):
            area = np.array([points[y, x], points[y, x + 1], points[y + 1, x], points[y + 1, x + 1]])
            yield ((x, y), area)


def get_map_inner(points):
    """
    Args:
        points (np.ndarray): N x 2 array.

    Yields:
        np.ndarray: (x, y).
    """
    points = np.array(points)
    if len(points.shape) == 1:
        points = np.array([points])

    return np.mean(points, axis=0)


def separate_edges(edges, inner):
    """
    Args:
        edges: A iterate object which contains float ot integer.
        inner (float, int): A inner point to separate edges.

    Returns:
        float, float: Lower edge and upper edge. if not found, return None
    """
    if len(edges) == 0:
        return None, None
    elif len(edges) == 1:
        edge = edges[0]
        return (None, edge) if edge > inner else (edge, None)
    else:
        lower = [edge for edge in edges if edge < inner]
        upper = [edge for edge in edges if edge > inner]
        lower = lower[0] if len(lower) else None
        upper = upper[-1] if len(upper) else None
        return lower, upper


def perspective_transform(points, data):
    """
    Args:
        points: A 2D array with shape (n, 2)
        data: Perspective data, a 2D array with shape (3, 3),
            see https://web.archive.org/web/20150222120106/xenia.media.mit.edu/~cwren/interpolator/

    Returns:
        np.ndarray: 2D array with shape (n, 2)
    """
    points = np.pad(np.array(points), ((0, 0), (0, 1)), mode='constant', constant_values=1)
    matrix = data.dot(points.T)
    x, y = matrix[0] / matrix[2], matrix[1] / matrix[2]
    points = np.array([x, y]).T
    return points


def fit_points(points, mod, encourage=1):
    """
    Get a closet point in a group of points with common difference.
    Will ignore points in the distance.

    Args:
        points: Points on image, a 2D array with shape (n, 2)
        mod: Common difference of points, (x, y).
        encourage (int, float): Describe how close to fit a group of points, in pixel.
            Smaller means closer to local minimum, larger means closer to global minimum.

    Returns:
        np.ndarray: (x, y)
    """
    encourage = np.square(encourage)
    mod = np.array(mod)
    points = np.array(points) % mod
    points = np.append(points - mod, points, axis=0)

    def cal_distance(point):
        distance = np.linalg.norm(points - point, axis=1)
        return np.sum(1 / (1 + np.exp(encourage / distance) / distance))

    # Fast local minimizer
    # result = optimize.minimize(cal_distance, np.mean(points, axis=0), method='SLSQP')
    # return result['x'] % mod

    # Brute-force global minimizer
    area = np.append(-mod - 10, mod + 10)
    result = optimize.brute(cal_distance, ((area[0], area[2]), (area[1], area[3])))
    return result % mod
