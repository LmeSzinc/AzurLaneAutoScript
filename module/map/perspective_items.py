import numpy as np


class Points:
    def __init__(self, points, config):
        if points is None:
            self._bool = False
            self.points = None
        else:
            self._bool = True
            self.points = np.array(points)
            if len(self.points.shape) == 1:
                self.points = np.array([self.points])
        self.config = config
        self.x, self.y = self.points.T

    def __str__(self):
        return str(self.points)

    def __iter__(self):
        return iter(self.points)

    def __getitem__(self, item):
        return self.points[item]

    def __len__(self):
        return len(self.points)

    def __bool__(self):
        return self._bool

    def link(self, point, is_horizontal=False):
        if is_horizontal:
            lines = [[y, np.pi/2] for y in self.y]
            return Lines(lines, is_horizontal=True, config=self.config)
        else:
            x, y = point
            theta = -np.arctan((self.x - x) / (self.y - y))
            rho = self.x * np.cos(theta) + self.y * np.sin(theta)
            lines = np.array([rho, theta]).T
            return Lines(lines, is_horizontal=False, config=self.config)


class Lines:
    def __init__(self, lines, is_horizontal, config):
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
        self.config = config

    def __str__(self):
        return str(self.lines)

    def __iter__(self):
        return iter(self.lines)

    def __getitem__(self, item):
        return Lines(self.lines[item], is_horizontal=self.is_horizontal, config=self.config)

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
            rho = x * np.cos(theta) + self.config.MID_Y * np.sin(theta)
            return np.array((rho, theta))

    @property
    def mid(self):
        if not self:
            return np.array([])
        if self.is_horizontal:
            return self.rho
        else:
            return (self.rho - self.config.MID_Y * self.sin) / self.cos

    def get_x(self, y):
        return (self.rho - y * self.sin) / self.cos

    def get_y(self, x):
        return (self.rho - x * self.cos) / self.sin

    def add(self, other):
        if not other:
            return self
        lines = np.append(self.lines, other.lines, axis=0)
        return Lines(lines, is_horizontal=self.is_horizontal, config=self.config)

    def move(self, x, y):
        if not self:
            return self
        if self.is_horizontal:
            self.lines[:, 0] += y
        else:
            self.lines[:, 0] += x * self.cos + y * self.sin
        return Lines(self.lines, is_horizontal=self.is_horizontal, config=self.config)

    def sort(self):
        if not self:
            return self
        lines = self.lines[np.argsort(self.mid)]
        return Lines(lines, is_horizontal=self.is_horizontal, config=self.config)

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
        regrouped = np.vstack([Lines(r, is_horizontal=self.is_horizontal, config=self.config).mean for r in regrouped])
        return Lines(regrouped, is_horizontal=self.is_horizontal, config=self.config)

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
        points = Points(points, config=self.config)
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

        return Lines(lines, is_horizontal=self.is_horizontal, config=self.config)
