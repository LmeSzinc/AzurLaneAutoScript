import re

import numpy as np
from PIL import Image

from module.base.mask import Mask
from module.ui.page import *

MASK_MAIN = Mask('./assets/mask/MASK_MAIN.png')
MASK_PLAYER = Mask('./assets/mask/MASK_PLAYER.png')


def put_image_mask(image, mask):
    """
    Args:
        image (PIL.Image.Image):
        mask (str): Filename

    Returns:
        PIL.Image.Image:
    """
    mask = Image.open(f'./assets/mask/{mask}.png').convert('L')
    new = Image.new('RGB', image.size, (0, 0, 0))
    new.paste(image, box=(0, 0, image.size[0], image.size[1]), mask=mask)
    return new


def handle_sensitive_image(image):
    """
    Args:
        image:

    Returns:
        PIL.Image.Image:
    """
    if PLAYER_CHECK.match(image, offset=(30, 30)):
        image = Image.fromarray(MASK_PLAYER.apply(image), mode='RGB')
    if MAIN_CHECK.match(image, offset=(30, 30)):
        image = Image.fromarray(MASK_MAIN.apply(image), mode='RGB')

    return image


def handle_sensitive_text(text):
    """
    Args:
        text (str):

    Returns:
        str:
    """
    text = re.sub('File \"(.*?)AzurLaneAutoScript', 'File \"C:\\\\fakepath\\\\AzurLaneAutoScript', text)
    return text


def handle_sensitive_logs(logs):
    return [handle_sensitive_text(line) for line in logs]
