import cv2
import numpy as np
from scipy import signal

from module.base.utils import image_size


def map_image_preprocess(image):
    """
    A shared preprocess method used in ResourceGenerate and _predict_position()

    Args:
        image (np.ndarray): Screenshot in RGB

    Returns:
        np.ndarray:
    """
    # image = rgb2luma(image)
    image = cv2.GaussianBlur(image, (5, 5), 0)
    image = cv2.Canny(image, 15, 50)
    return image


def create_circular_mask(h, w, center=None, radius=None):
    # https://stackoverflow.com/questions/44865023/how-can-i-create-a-circular-mask-for-a-numpy-array
    if center is None:  # use the middle of the image
        center = (int(w / 2), int(h / 2))
    if radius is None:  # use the smallest distance between the center and image walls
        radius = min(center[0], center[1], w - center[0], h - center[1])

    y, x = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2)

    mask = dist_from_center <= radius
    return mask


def rotate_bound(image, angle):
    """
    Rotate an image with outbound

    https://blog.csdn.net/qq_37674858/article/details/80708393

    Args:
        image (np.ndarray):
        angle (int, float):

    Returns:
        np.ndarray:
    """
    # grab the dimensions of the image and then determine the
    # center
    (h, w) = image.shape[:2]
    (cX, cY) = (w // 2, h // 2)

    # grab the rotation matrix (applying the negative of the
    # angle to rotate clockwise), then grab the sine and cosine
    # (i.e., the rotation components of the matrix)
    M = cv2.getRotationMatrix2D((cX, cY), -angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])

    # compute the new bounding dimensions of the image
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))

    # adjust the rotation matrix to take into account translation
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY

    # perform the actual rotation and return the image
    return cv2.warpAffine(image, M, (nW, nH))


def cubic_find_maximum(image, precision=0.05):
    """
    Using CUBIC resize algorithm to fit a curved surface, find the maximum value and location.

    Args:
        image (np.ndarray):
        precision (int, float):

    Returns:
        float: Maximum value on curved surface
        np.ndarray[float, float]: Location of maximum value
    """
    image = cv2.resize(image, None, fx=1 / precision, fy=1 / precision, interpolation=cv2.INTER_CUBIC)
    _, sim, _, loca = cv2.minMaxLoc(image)
    loca = np.array(loca, dtype=float) * precision
    return sim, loca


def image_center_pad(image, size, value=(0, 0, 0)):
    """
    Create a new image with given `size`, placing given `image` in the middle.

    Args:
        image (np.ndarray):
        size: (width, height)
        value: Color of the background.

    Returns:
        np.ndarray:
    """
    diff = np.array(size) - image_size(image)
    left, top = int(diff[0] / 2), int(diff[1] / 2)
    right, bottom = diff[0] - left, diff[1] - top
    image = cv2.copyMakeBorder(image, top, bottom, left, right, borderType=cv2.BORDER_CONSTANT, value=value)
    return image


def image_center_crop(image, size):
    """
    Center crop the given image.

    Args:
        image (np.ndarray):
        size: Output image shape, (width, height)

    Returns:
        np.ndarray:
    """
    diff = image_size(image) - np.array(size)
    left, top = int(diff[0] / 2), int(diff[1] / 2)
    right, bottom = diff[0] - left, diff[1] - top
    image = image[top:-bottom, left:-right]
    return image


def area2corner(area):
    """
    Args:
        area: (x1, y1, x2, y2)

    Returns:
        np.ndarray: [upper-left, upper-right, bottom-left, bottom-right]
    """
    return np.array([[area[0], area[1]], [area[2], area[1]], [area[0], area[3]], [area[2], area[3]]])


def convolve(arr, kernel=3):
    """
    Args:
        arr (np.ndarray): Shape (N,)
        kernel (int):

    Returns:
        np.ndarray:
    """
    return sum(np.roll(arr, i) * (kernel - abs(i)) // kernel for i in range(-kernel + 1, kernel))


def convolve_plain(arr, kernel=3):
    """
    Args:
        arr (np.ndarray): Shape (N,)
        kernel (int):

    Returns:
        np.ndarray:
    """
    return sum(np.roll(arr, i) for i in range(-kernel + 1, kernel))


def peak_confidence(arr, **kwargs):
    """
    Evaluate the prominence of the highest peak

    Args:
        arr (np.ndarray): Shape (N,)
        **kwargs: Additional kwargs for signal.find_peaks

    Returns:
        float: 0-1
    """
    para = {
        'height': 0,
        'prominence': 10,
    }
    para.update(kwargs)
    length = len(arr)
    peaks, properties = signal.find_peaks(np.concatenate((arr, arr, arr)), **para)
    peaks = [h for p, h in zip(peaks, properties['peak_heights']) if length <= p < length * 2]
    peaks = sorted(peaks, reverse=True)

    count = len(peaks)
    if count > 1:
        highest, second = peaks[0], peaks[1]
    elif count == 1:
        highest, second = 1, 0
    else:
        highest, second = 1, 0
    confidence = (highest - second) / highest
    return confidence
