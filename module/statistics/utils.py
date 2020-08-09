import os

from PIL import Image


class ImageError(Exception):
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


def load_image(file):
    """
    Args:
        file (str): Path to file.

    Returns:
        Pillow image.
    """
    return Image.open(file).convert('RGB')
