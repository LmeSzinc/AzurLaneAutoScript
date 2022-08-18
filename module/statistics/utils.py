import os

import cv2
import numpy as np

from module.base.utils import crop, image_size


class ImageError(Exception):
    """ Error when parsing images """
    pass


class ImageInvalidResolution(ImageError):
    """ Image is not in 1280x720 """
    pass


def load_folder(folder):
    """
    Args:
        folder (str): Template folder contains images.
            Image shape: width=96, height=96, channel=3, format=png.
            Image name: Camel-Case, such as 'PlateGeneralT3'. Suffix in name will be ignore.
            For example, 'Javelin' and 'Javelin_2' are different templates, but have same output name 'Javelin'.

    Returns:
        dict: Key: str, image file base name. Value: full filepath.
    """
    if not os.path.exists(folder):
        return {}

    out = {}
    for file in os.listdir(folder):
        name = os.path.splitext(file)[0]
        out[name] = os.path.join(folder, file)

    return out


def pack(img_list):
    """
    Stack images vertically.

    Args:
        img_list (list): List of image

    Returns:
        np.ndarray:
    """
    image = cv2.vconcat(img_list)
    return image


def unpack(image):
    """
    Split images vertically.

    Args:
        image:

    Returns:
        list: List of np.ndarray.
    """
    size = image_size(image)
    if size == (1280, 720):
        return [image]
    else:
        if size[0] != 1280 or size[1] % 720 != 0:
            raise ImageInvalidResolution(f'Unexpected image size: {size}')
        return [crop(image, (0, n * 720, 1280, (n + 1) * 720)) for n in range(size[1] // 720)]
