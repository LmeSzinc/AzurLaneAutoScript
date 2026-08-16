import cv2
import numpy as np
from PIL import Image


def load_image(file, area=None):
    """
    Load an image like pillow and drop alpha channel.

    Args:
        file (str):
        area (tuple):

    Returns:
        np.ndarray:
    """
    # always remember to close Image object
    with Image.open(file) as f:
        if area is not None:
            f = f.crop(area)

        image = np.array(f)

    channel = image_channel(image)
    if channel == 4:
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)

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


def copy_image(src):
    """
    Equivalent to image.copy() but a little bit faster

    Time cost to copy a 1280*720*3 image:
        image.copy()      0.743ms
        copy_image(image) 0.639ms
    """
    # cv2.copyTo(src, None, dst) 3-arg form was removed in opencv 4.11
    return cv2.copyTo(src, None)


def crop(image, area, copy=True):
    """
    Crop image like pillow, when using opencv / numpy.
    Provides a black background if cropping outside of image.

    Args:
        image (np.ndarray):
        area:
        copy (bool):

    Returns:
        np.ndarray:
    """
    # map(round, area)
    x1, y1, x2, y2 = area
    x1 = round(x1)
    y1 = round(y1)
    x2 = round(x2)
    y2 = round(y2)
    # h, w = image.shape[:2]
    shape = image.shape
    h = shape[0]
    w = shape[1]
    # top, bottom, left, right
    # border = np.maximum((0 - y1, y2 - h, 0 - x1, x2 - w), 0)
    overflow = False
    if y1 >= 0:
        top = 0
        if y1 >= h:
            overflow = True
    else:
        top = -y1
    if y2 > h:
        bottom = y2 - h
    else:
        bottom = 0
        if y2 <= 0:
            overflow = True
    if x1 >= 0:
        left = 0
        if x1 >= w:
            overflow = True
    else:
        left = -x1
    if x2 > w:
        right = x2 - w
    else:
        right = 0
        if x2 <= 0:
            overflow = True
    # If overflowed, return empty image
    if overflow:
        if len(shape) == 2:
            size = (y2 - y1, x2 - x1)
        else:
            size = (y2 - y1, x2 - x1, shape[2])
        return np.zeros(size, dtype=image.dtype)
    # x1, y1, x2, y2 = np.maximum((x1, y1, x2, y2), 0)
    if x1 < 0:
        x1 = 0
    if y1 < 0:
        y1 = 0
    if x2 < 0:
        x2 = 0
    if y2 < 0:
        y2 = 0
    # crop image
    image = image[y1:y2, x1:x2]
    # if border
    if top or bottom or left or right:
        if len(shape) == 2:
            value = 0
        else:
            value = tuple(0 for _ in range(image.shape[2]))
        return cv2.copyMakeBorder(image, top, bottom, left, right, borderType=cv2.BORDER_CONSTANT, value=value)
    elif copy:
        return copy_image(image)
    else:
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


def image_paste(image, background, origin):
    """
    Paste an image on background.
    This method does not return a value, but instead updates the array "background".

    Args:
        image:
        background:
        origin: Upper-left corner, (x, y)
    """
    x, y = origin
    w, h = image_size(image)
    background[y : y + h, x : x + w] = image


def rgb2gray(image):
    """
    gray = ( MAX(r, g, b) + MIN(r, g, b)) / 2

    Args:
        image (np.ndarray): Shape (height, width, channel)

    Returns:
        np.ndarray: Shape (height, width)
    """
    # r, g, b = cv2.split(image)
    # return cv2.add(
    #     cv2.multiply(cv2.max(cv2.max(r, g), b), 0.5),
    #     cv2.multiply(cv2.min(cv2.min(r, g), b), 0.5)
    # )
    r, g, b = cv2.split(image)
    maximum = cv2.max(r, g)
    cv2.min(r, g, dst=r)
    cv2.max(maximum, b, dst=maximum)
    cv2.min(r, b, dst=r)
    # minimum = r
    cv2.convertScaleAbs(maximum, alpha=0.5, dst=maximum)
    cv2.convertScaleAbs(r, alpha=0.5, dst=r)
    cv2.add(maximum, r, dst=maximum)
    return maximum


def rgb2hsv(image):
    """
    Convert RGB color space to HSV color space.
    HSV is Hue Saturation Value.

    Args:
        image (np.ndarray): Shape (height, width, channel)

    Returns:
        np.ndarray: Hue (0~360), Saturation (0~100), Value (0~100).
    """
    image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(float)
    cv2.multiply(image, (360 / 180, 100 / 255, 100 / 255, 0), dst=image)
    return image


def rgb2yuv(image):
    """
    Convert RGB to YUV color space.

    Args:
        image (np.ndarray): Shape (height, width, channel)

    Returns:
        np.ndarray: Shape (height, width)
    """
    image = cv2.cvtColor(image, cv2.COLOR_RGB2YUV)
    return image


def rgb2luma(image):
    """
    Convert RGB to the Y channel (Luminance) in YUV color space.

    Args:
        image (np.ndarray): Shape (height, width, channel)

    Returns:
        np.ndarray: Shape (height, width)
    """
    image = cv2.cvtColor(image, cv2.COLOR_RGB2YUV)
    luma, _, _ = cv2.split(image)
    return luma


def get_bbox(image, threshold=0):
    """
    Get outbound box of the content in image
    A opencv implementation of the getbbox() in pillow

    Args:
        image (np.ndarray):
        threshold (int):
            color > threshold will be considered as content
            color <= threshold will be considered background

    Returns:
        tuple[int, int, int, int]: area

    Raises:
        ImageNotSupported: if failed to get bbox
    """
    channel = image_channel(image)
    # convert to grayscale
    if channel == 3:
        # RGB
        mask = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        cv2.threshold(mask, threshold, 255, cv2.THRESH_BINARY, dst=mask)
    elif channel == 0:
        # grayscale
        _, mask = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)
    elif channel == 4:
        # RGBA
        mask = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
        cv2.threshold(mask, threshold, 255, cv2.THRESH_BINARY, dst=mask)
    else:
        raise ImageNotSupported(f"shape={image.shape}")

    # find bbox
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_y, min_x = mask.shape
    max_x = 0
    max_y = 0
    # all black
    if not contours:
        raise ImageNotSupported("Cannot get bbox from a pure black image")
    for contour in contours:
        # x, y, w, h
        x1, y1, x2, y2 = cv2.boundingRect(contour)
        x2 += x1
        y2 += y1
        if x1 < min_x:
            min_x = x1
        if y1 < min_y:
            min_y = y1
        if x2 > max_x:
            max_x = x2
        if y2 > max_y:
            max_y = y2
    if min_x < max_x and min_y < max_y:
        return min_x, min_y, max_x, max_y
    else:
        # This shouldn't happen
        raise ImageNotSupported(f"Empty bbox {(min_x, min_y, max_x, max_y)}")


def get_bbox_reversed(image, threshold=255):
    """
    Get outbound box of the content in image
    A opencv implementation of the getbbox() in pillow

    Args:
        image (np.ndarray):
        threshold (int):
            color < threshold will be considered as content
            color >= threshold will be considered background

    Returns:
        tuple[int, int, int, int]: area

    Raises:
        ImageNotSupported: if failed to get bbox
    """
    channel = image_channel(image)
    # convert to grayscale
    if channel == 3:
        # RGB
        mask = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        cv2.threshold(mask, 0, threshold, cv2.THRESH_BINARY, dst=mask)
    elif channel == 0:
        # grayscale
        mask = cv2.threshold(image, 0, threshold, cv2.THRESH_BINARY)
    elif channel == 4:
        # RGBA
        mask = cv2.cvtColor(image, cv2.COLOR_RGBA2GRAY)
        cv2.threshold(mask, 0, threshold, cv2.THRESH_BINARY, dst=mask)
    else:
        raise ImageNotSupported(f"shape={image.shape}")

    # find bbox
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_y, min_x = mask.shape
    max_x = 0
    max_y = 0
    # all black
    if not contours:
        raise ImageNotSupported("Cannot get bbox from a pure black image")
    for contour in contours:
        # x, y, w, h
        x1, y1, x2, y2 = cv2.boundingRect(contour)
        x2 += x1
        y2 += y1
        if x1 < min_x:
            min_x = x1
        if y1 < min_y:
            min_y = y1
        if x2 > max_x:
            max_x = x2
        if y2 > max_y:
            max_y = y2
    if min_x < max_x and min_y < max_y:
        return min_x, min_y, max_x, max_y
    else:
        # This shouldn't happen
        raise ImageNotSupported(f"Empty bbox {(min_x, min_y, max_x, max_y)}")


def extract_letters(image, letter=(255, 255, 255), threshold=128):
    """Set letter color to black, set background color to white.

    Args:
        image: Shape (height, width, channel)
        letter (tuple): Letter RGB.
        threshold (int):

    Returns:
        np.ndarray: Shape (height, width)
    """
    # r, g, b = cv2.split(cv2.subtract(image, (*letter,)))
    # positive = cv2.max(cv2.max(r, g), b)
    # r, g, b = cv2.split(cv2.subtract((*letter, 0), image))
    # negative = cv2.max(cv2.max(r, g), b)
    # return cv2.multiply(cv2.add(positive, negative), 255.0 / threshold)
    diff = cv2.subtract(image, (*letter,))
    r, g, b = cv2.split(diff)
    cv2.max(r, g, dst=r)
    cv2.max(r, b, dst=r)
    positive = r
    cv2.subtract((*letter,), image, dst=diff)
    r, g, b = cv2.split(diff)
    cv2.max(r, g, dst=r)
    cv2.max(r, b, dst=r)
    negative = r
    cv2.add(positive, negative, dst=positive)
    if threshold != 255:
        cv2.convertScaleAbs(positive, alpha=255.0 / threshold, dst=positive)
    return positive


def extract_white_letters(image, threshold=128):
    """Set letter color to black, set background color to white.
    This function will discourage color pixels (Non-gray pixels)

    Args:
        image: Shape (height, width, channel)
        threshold (int):

    Returns:
        np.ndarray: Shape (height, width)
    """
    # minimum = cv2.min(cv2.min(r, g), b)
    # maximum = cv2.max(cv2.max(r, g), b)
    # return cv2.multiply(cv2.add(maximum, cv2.subtract(maximum, minimum)), 255.0 / threshold)
    r, g, b = cv2.split(cv2.subtract((255, 255, 255), image))
    maximum = cv2.max(r, g)
    cv2.min(r, g, dst=r)
    cv2.max(maximum, b, dst=maximum)
    cv2.min(r, b, dst=r)
    # minimum = r

    cv2.convertScaleAbs(maximum, alpha=0.5, dst=maximum)
    cv2.convertScaleAbs(r, alpha=0.5, dst=r)
    cv2.subtract(maximum, r, dst=r)
    cv2.add(maximum, r, dst=maximum)
    if threshold != 255:
        cv2.convertScaleAbs(maximum, alpha=255.0 / threshold, dst=maximum)
    return maximum


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
    # image = cv2.add(cv2.multiply(image, multiply), add)
    cv2.multiply(image, multiply, dst=image)
    cv2.add(image, add, dst=image)
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


class ImageNotSupported(Exception):
    """
    Raised if we can't perform image calculation on this image
    """

    pass
