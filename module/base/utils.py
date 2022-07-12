import cv2
import numpy as np
from PIL import Image


def random_normal_distribution_int(a, b, n=3):
    """Generate a normal distribution int within the interval. Use the average value of several random numbers to
    simulate normal distribution.

    Args:
        a (int): The minimum of the interval.
        b (int): The maximum of the interval.
        n (int): The amount of numbers in simulation. Default to 3.

    Returns:
        int
    """
    if a < b:
        output = np.mean(np.random.randint(a, b, size=n))
        return int(output.round())
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
    vector = np.round(vector).astype(np.int)
    half_vector = np.round(vector / 2).astype(np.int)
    box = np.array(box) + np.append(np.abs(half_vector) + padding, -np.abs(half_vector) - padding)
    center = random_rectangle_point(box)
    start_point = center - half_vector
    end_point = start_point + vector
    return tuple(start_point), tuple(end_point)


def random_rectangle_vector_opted(
        vector, box, random_range=(0, 0, 0, 0), padding=15, whitelist_area=None, blacklist_area=None):
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
    vector = np.round(vector).astype(np.int)
    half_vector = np.round(vector / 2).astype(np.int)
    box_pad = np.array(box) + np.append(np.abs(half_vector) + padding, -np.abs(half_vector) - padding)
    box_pad = area_offset(box_pad, half_vector)
    segment = int(np.linalg.norm(vector) // 70) + 1

    def in_blacklist(end):
        if not blacklist_area:
            return False
        for x in range(segment + 1):
            point = - vector * x / segment + end
            for area in blacklist_area:
                if point_in_area(point, area, threshold=0):
                    return True
        return False

    if whitelist_area:
        for area in whitelist_area:
            area = area_limit(area, box_pad)
            if all([x > 0 for x in area_size(area)]):
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
    return [tuple((((n - index) * p1 + index * p2) / n).astype(int) + random_rectangle_point(random_range))
            for index in range(0, n + 1)]


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
        multiply = 10 ** precision
        result = random_normal_distribution_int(second[0] * multiply, second[1] * multiply, n) / multiply
        return round(result, precision)
    elif isinstance(second, str):
        if ',' in second:
            lower, upper = second.replace(' ', '').split(',')
            lower, upper = int(lower), int(upper)
            return ensure_time((lower, upper), n=n, precision=precision)
        if '-' in second:
            lower, upper = second.replace(' ', '').split('-')
            lower, upper = int(lower), int(upper)
            return ensure_time((lower, upper), n=n, precision=precision)
        else:
            return int(second)
    else:
        return second


def ensure_int(*args):
    """
    Convert all elements to int.
    Return the same structure as nested objects.

    Args:
        *args:

    Returns:
        list:
    """
    def to_int(item):
        try:
            return int(item)
        except TypeError:
            result = [to_int(i) for i in item]
            if len(result) == 1:
                result = result[0]
            return result

    return to_int(args)


def area_offset(area, offset):
    """

    Args:
        area: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        offset: (x, y).

    Returns:
        tuple: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
    """
    return tuple(np.array(area) + np.append(offset, offset))


def area_pad(area, pad=10):
    """

    Args:
        area: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        pad (int):

    Returns:
        tuple: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
    """
    return tuple(np.array(area) + np.array([pad, pad, -pad, -pad]))


def limit_in(x, lower, upper):
    """
    Limit x within range (lower, upper)

    Args:
        x:
        lower:
        upper:

    Returns:
        int, float:
    """
    return max(min(x, upper), lower)


def area_limit(area1, area2):
    """
    Limit an area in another area.

    Args:
        area1: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        area2: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).

    Returns:
        tuple: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
    """
    x_lower, y_lower, x_upper, y_upper = area2
    return (
        limit_in(area1[0], x_lower, x_upper),
        limit_in(area1[1], y_lower, y_upper),
        limit_in(area1[2], x_lower, x_upper),
        limit_in(area1[3], y_lower, y_upper),
    )


def area_size(area):
    """
    Area size or shape.

    Args:
        area: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).

    Returns:
        tuple: (x, y).
    """
    return (
        max(area[2] - area[0], 0),
        max(area[3] - area[1], 0)
    )


def point_limit(point, area):
    """
    Limit point in an area.

    Args:
        point: (x, y).
        area: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).

    Returns:
        tuple: (x, y).
    """
    return (
        limit_in(point[0], area[0], area[2]),
        limit_in(point[1], area[1], area[3])
    )


def point_in_area(point, area, threshold=5):
    """

    Args:
        point: (x, y).
        area: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        threshold: int

    Returns:
        bool:
    """
    return area[0] - threshold < point[0] < area[2] + threshold and area[1] - threshold < point[1] < area[3] + threshold


def area_in_area(area1, area2, threshold=5):
    """

    Args:
        area1: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        area2: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        threshold: int

    Returns:
        bool:
    """
    return area2[0] - threshold <= area1[0] \
           and area2[1] - threshold <= area1[1] \
           and area1[2] <= area2[2] + threshold \
           and area1[3] <= area2[3] + threshold


def area_cross_area(area1, area2, threshold=5):
    """

    Args:
        area1: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        area2: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y).
        threshold: int

    Returns:
        bool:
    """
    return point_in_area((area1[0], area1[1]), area2, threshold=threshold) \
           or point_in_area((area1[2], area1[1]), area2, threshold=threshold) \
           or point_in_area((area1[0], area1[3]), area2, threshold=threshold) \
           or point_in_area((area1[2], area1[3]), area2, threshold=threshold)


def float2str(n, decimal=3):
    """
    Args:
        n (float):
        decimal (int):

    Returns:
        str:
    """
    return str(round(n, decimal)).ljust(decimal + 2, "0")


def point2str(x, y, length=4):
    """
    Args:
        x (int, float):
        y (int, float):
        length (int): Align length.

    Returns:
        str: String with numbers right aligned, such as '( 100,  80)'.
    """
    return '(%s, %s)' % (str(int(x)).rjust(length), str(int(y)).rjust(length))


def node2location(node):
    """
    Args:
        node(str): Example: 'E3'

    Returns:
        tuple: Example: (6, 4)
    """
    return ord(node[0]) % 32 - 1, int(node[1:]) - 1


def location2node(location):
    """
    Args:
        location(tuple): Example: (6, 4)

    Returns:
        str: Example: 'E3'
    """
    return chr(location[0] + 64 + 1) + str(location[1] + 1)


def load_image(file, area=None):
    """
    Load an image like pillow and drop alpha channel.

    Args:
        file (str):
        area (tuple):

    Returns:
        np.ndarray:
    """
    image = Image.open(file)
    if area is not None:
        image = image.crop(area)
    image = np.array(image)
    channel = image.shape[2] if len(image.shape) > 2 else 1
    if channel > 3:
        image = image[:, :, :3].copy()
    return image


def save_image(image, file):
    """
    Save an image like pillow.

    Args:
        image (np.ndarray):
        file (str):
    """
    # image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    # cv2.imwrite(file, image)
    Image.fromarray(image).save(file)


def crop(image, area):
    """
    Crop image like pillow, when using opencv / numpy.
    Provides a black background if cropping outside of image.

    Args:
        image (np.ndarray):
        area:

    Returns:
        np.ndarray:
    """
    x1, y1, x2, y2 = map(int, map(round, area))
    h, w = image.shape[:2]
    border = np.maximum((0 - y1, y2 - h, 0 - x1, x2 - w), 0)
    x1, y1, x2, y2 = np.maximum((x1, y1, x2, y2), 0)
    image = image[y1:y2, x1:x2].copy()
    if sum(border) > 0:
        image = cv2.copyMakeBorder(image, *border, borderType=cv2.BORDER_CONSTANT, value=(0, 0, 0))
    return image


def resize(image, size):
    """
    Resize image like pillow image.resize(), but implement in opencv.
    Pillow uses PIL.Image.NEAREST by default.

    Args:
        image (np.ndarray):
        size: (x, y)

    Returns:
        np.ndarray:
    """
    return cv2.resize(image, size, interpolation=cv2.INTER_NEAREST)


def image_channel(image):
    """
    Args:
        image (np.ndarray):

    Returns:
        int: 0 for grayscale, 3 for RGB.
    """
    return image.shape[2] if len(image.shape) == 3 else 0


def image_size(image):
    """
    Args:
        image (np.ndarray):

    Returns:
        int, int: width, height
    """
    shape = image.shape
    return shape[1], shape[0]


def rgb2gray(image):
    """
    Args:
        image (np.ndarray): Shape (height, width, channel)

    Returns:
        np.ndarray: Shape (height, width)
    """
    r, g, b = cv2.split(image)
    return cv2.add(
        cv2.multiply(cv2.max(cv2.max(r, g), b), 0.5),
        cv2.multiply(cv2.min(cv2.min(r, g), b), 0.5)
    )


def rgb2hsv(image):
    """
    Convert RGB color space to HSV color space.
    HSV is Hue Saturation Value.

    Args:
        image (np.ndarray): Shape (height, width, channel)

    Returns:
        np.ndarray: Hue (0~360), Saturation (0~100), Value (0~100).
    """
    image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float)
    image *= (360 / 180, 100 / 255, 100 / 255)
    return image


def get_color(image, area):
    """Calculate the average color of a particular area of the image.

    Args:
        image (np.ndarray): Screenshot.
        area (tuple): (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y)

    Returns:
        tuple: (r, g, b)
    """
    temp = crop(image, area)
    color = cv2.mean(temp)
    return color[:3]


def get_bbox(image):
    """
    A numpy implementation of the getbbox() in pillow.

    Args:
        image (np.ndarray): Screenshot.

    Returns:
        tuple: (upper_left_x, upper_left_y, bottom_right_x, bottom_right_y)
    """
    if image_channel(image) == 3:
        image = np.max(image, axis=2)
    x = np.where(np.max(image, axis=0) > 0)[0]
    y = np.where(np.max(image, axis=1) > 0)[0]
    return (x[0], y[0], x[-1] + 1, y[-1] + 1)


def color_similarity(color1, color2):
    """
    Args:
        color1 (tuple): (r, g, b)
        color2 (tuple): (r, g, b)

    Returns:
        int:
    """
    diff = np.array(color1).astype(int) - np.array(color2).astype(int)
    diff = np.max(np.maximum(diff, 0)) - np.min(np.minimum(diff, 0))
    return diff


def color_similar(color1, color2, threshold=10):
    """Consider two colors are similar, if tolerance lesser or equal threshold.
    Tolerance = Max(Positive(difference_rgb)) + Max(- Negative(difference_rgb))
    The same as the tolerance in Photoshop.

    Args:
        color1 (tuple): (r, g, b)
        color2 (tuple): (r, g, b)
        threshold (int): Default to 10.

    Returns:
        bool: True if two colors are similar.
    """
    # print(color1, color2)
    diff = np.array(color1).astype(int) - np.array(color2).astype(int)
    diff = np.max(np.maximum(diff, 0)) - np.min(np.minimum(diff, 0))
    return diff <= threshold


def color_similar_1d(image, color, threshold=10):
    """
    Args:
        image (np.ndarray): 1D array.
        color: (r, g, b)
        threshold(int): Default to 10.

    Returns:
        np.ndarray: bool
    """
    diff = image.astype(int) - color
    diff = np.max(np.maximum(diff, 0), axis=1) - np.min(np.minimum(diff, 0), axis=1)
    return diff <= threshold


def color_similarity_2d(image, color):
    """
    Args:
        image: 2D array.
        color: (r, g, b)

    Returns:
        np.ndarray: uint8
    """
    r, g, b = cv2.split(cv2.subtract(image, (*color, 0)))
    positive = cv2.max(cv2.max(r, g), b)
    r, g, b = cv2.split(cv2.subtract((*color, 0), image))
    negative = cv2.max(cv2.max(r, g), b)
    return cv2.subtract(255, cv2.add(positive, negative))


def extract_letters(image, letter=(255, 255, 255), threshold=128):
    """Set letter color to black, set background color to white.

    Args:
        image: Shape (height, width, channel)
        letter (tuple): Letter RGB.
        threshold (int):

    Returns:
        np.ndarray: Shape (height, width)
    """
    r, g, b = cv2.split(cv2.subtract(image, (*letter, 0)))
    positive = cv2.max(cv2.max(r, g), b)
    r, g, b = cv2.split(cv2.subtract((*letter, 0), image))
    negative = cv2.max(cv2.max(r, g), b)
    return cv2.multiply(cv2.add(positive, negative), 255.0 / threshold)


def extract_white_letters(image, threshold=128):
    """Set letter color to black, set background color to white.
    This function will discourage color pixels (Non-gray pixels)

    Args:
        image: Shape (height, width, channel)
        threshold (int):

    Returns:
        np.ndarray: Shape (height, width)
    """
    r, g, b = cv2.split(cv2.subtract((255, 255, 255, 0), image))
    minimum = cv2.min(cv2.min(r, g), b)
    maximum = cv2.max(cv2.max(r, g), b)
    return cv2.multiply(cv2.add(maximum, cv2.subtract(maximum, minimum)), 255.0 / threshold)


def color_mapping(image, max_multiply=2):
    """
    Mapping color to 0-255.
    Minimum color to 0, maximum color to 255, multiply colors by 2 at max.

    Args:
        image (np.ndarray):
        max_multiply (int, float):

    Returns:
        np.ndarray:
    """
    image = image.astype(float)
    low, high = np.min(image), np.max(image)
    multiply = min(255 / (high - low), max_multiply)
    add = (255 - multiply * (low + high)) / 2
    image = cv2.add(cv2.multiply(image, multiply), add)
    image[image > 255] = 255
    image[image < 0] = 0
    return image.astype(np.uint8)


def image_left_strip(image, threshold, length):
    """
    In `DAILY:200/200` strip `DAILY:` and leave `200/200`

    Args:
        image (np.ndarray): (height, width)
        threshold (int):
            0-255
            The first column with brightness lower than this
            will be considered as left edge.
        length (int):
            Strip this length of image after the left edge

    Returns:
        np.ndarray:
    """
    brightness = np.mean(image, axis=0)
    match = np.where(brightness < threshold)[0]

    if len(match):
        left = match[0] + length
        total = image.shape[1]
        if left < total:
            image = image[:, left:]
    return image


def red_overlay_transparency(color1, color2, red=247):
    """Calculate the transparency of red overlay.

    Args:
        color1: origin color.
        color2: changed color.
        red(int): red color 0-255. Default to 247.

    Returns:
        float: 0-1
    """
    return (color2[0] - color1[0]) / (red - color1[0])


def color_bar_percentage(image, area, prev_color, reverse=False, starter=0, threshold=30):
    """
    Args:
        image:
        area:
        prev_color:
        reverse: True if bar goes from right to left.
        starter:
        threshold:

    Returns:
        float: 0 to 1.
    """
    image = crop(image, area)
    image = image[:, ::-1, :] if reverse else image
    length = image.shape[1]
    prev_index = starter

    for _ in range(1280):
        bar = color_similarity_2d(image, color=prev_color)
        index = np.where(np.any(bar > 255 - threshold, axis=0))[0]
        if not index.size:
            return prev_index / length
        else:
            index = index[-1]
        if index <= prev_index:
            return index / length
        prev_index = index

        prev_row = bar[:, prev_index] > 255 - threshold
        if not prev_row.size:
            return prev_index / length
        prev_color = np.mean(image[:, prev_index], axis=0)

    return 0.
