import random

import numpy as np

from module.core.geometry import area_limit, area_offset, area_size, point_in_area, point_limit


def random_normal_distribution_int(a, b, n=3):
    """
    Generate a normal distribution int within the interval.
    Use the average value of several random numbers to simulate normal distribution.

    Args:
        a (int): The minimum of the interval.
        b (int): The maximum of the interval.
        n (int): The amount of numbers in simulation. Default to 3.

    Returns:
        int
    """
    a = round(a)
    b = round(b)
    if a < b:
        total = 0
        for _ in range(n):
            total += random.randint(a, b)
        return round(total / n)
    else:
        return b


def random_rectangle_point(area, n=3):
    """Choose a random point in an area.

    Args:
        area: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        n (int): The amount of numbers in simulation. Default to 3.

    Returns:
        tuple(int): (x, y)
    """
    x = random_normal_distribution_int(area[0], area[2], n=n)
    y = random_normal_distribution_int(area[1], area[3], n=n)
    return x, y


def random_rectangle_vector(vector, box, random_range=(0, 0, 0, 0), padding=15):
    """Place a vector in a box randomly.

    Args:
        vector: (x, y)
        box: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        random_range (tuple): Add a random_range to vector. (x_min, y_min, x_max, y_max).
        padding (int):

    Returns:
        tuple(int), tuple(int): start_point, end_point.
    """
    vector = np.array(vector) + random_rectangle_point(random_range)
    vector = np.round(vector).astype(int)
    half_vector = np.round(vector / 2).astype(int)
    box = np.array(box) + np.append(np.abs(half_vector) + padding, -np.abs(half_vector) - padding)
    center = random_rectangle_point(box)
    start_point = center - half_vector
    end_point = start_point + vector
    return tuple(start_point), tuple(end_point)


def random_rectangle_vector_opted(
    vector, box, random_range=(0, 0, 0, 0), padding=15, whitelist_area=None, blacklist_area=None
):
    """
    Place a vector in a box randomly.

    When emulator/game stuck, it treats a swipe as a click, clicking at the end of swipe path.
    To prevent this, random results need to be filtered.

    Args:
        vector: (x, y)
        box: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        random_range (tuple): Add a random_range to vector. (x_min, y_min, x_max, y_max).
        padding (int):
        whitelist_area: (list[tuple[int]]):
            A list of area that safe to click. Swipe path will end there.
        blacklist_area: (list[tuple[int]]):
            If none of the whitelist_area satisfies current vector, blacklist_area will be used.
            Delete random path that ends in any blacklist_area.

    Returns:
        tuple(int), tuple(int): start_point, end_point.
    """
    vector = np.array(vector) + random_rectangle_point(random_range)
    vector = np.round(vector).astype(int)
    half_vector = np.round(vector / 2).astype(int)
    box_pad = np.array(box) + np.append(np.abs(half_vector) + padding, -np.abs(half_vector) - padding)
    box_pad = area_offset(box_pad, half_vector)
    segment = int(np.linalg.norm(vector) // 70) + 1

    def in_blacklist(end):
        if not blacklist_area:
            return False
        for x in range(segment + 1):
            point = -vector * x / segment + end
            for area in blacklist_area:
                if point_in_area(point, area, threshold=0):
                    return True
        return False

    if whitelist_area:
        for area in whitelist_area:
            area = area_limit(area, box_pad)
            if all(x > 0 for x in area_size(area)):
                end_point = random_rectangle_point(area)
                for _ in range(10):
                    if in_blacklist(end_point):
                        continue
                    return point_limit(end_point - vector, box), point_limit(end_point, box)

    for _ in range(100):
        end_point = random_rectangle_point(box_pad)
        if in_blacklist(end_point):
            continue
        return point_limit(end_point - vector, box), point_limit(end_point, box)

    end_point = random_rectangle_point(box_pad)
    return point_limit(end_point - vector, box), point_limit(end_point, box)


def random_line_segments(p1, p2, n, random_range=(0, 0, 0, 0)):
    """Cut a line into multiple segments.

    Args:
        p1: (x, y).
        p2: (x, y).
        n: Number of slice.
        random_range: Add a random_range to points.

    Returns:
        list[tuple]: [(x0, y0), (x1, y1), (x2, y2)]
    """
    return [
        tuple((((n - index) * p1 + index * p2) / n).astype(int) + random_rectangle_point(random_range))
        for index in range(0, n + 1)
    ]


def ensure_time(second, n=3, precision=3):
    """Ensure to be time.

    Args:
        second (int, float, tuple): time, such as 10, (10, 30), '10, 30'
        n (int): The amount of numbers in simulation. Default to 5.
        precision (int): Decimals.

    Returns:
        float:
    """
    if isinstance(second, tuple):
        multiply = 10**precision
        result = random_normal_distribution_int(second[0] * multiply, second[1] * multiply, n) / multiply
        return round(result, precision)
    elif isinstance(second, str):
        if "," in second:
            lower, upper = second.replace(" ", "").split(",")
            lower, upper = int(lower), int(upper)
            return ensure_time((lower, upper), n=n, precision=precision)
        if "-" in second:
            lower, upper = second.replace(" ", "").split("-")
            lower, upper = int(lower), int(upper)
            return ensure_time((lower, upper), n=n, precision=precision)
        else:
            return int(second)
    else:
        return second
