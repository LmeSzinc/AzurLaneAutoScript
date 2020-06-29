from PIL import Image

from module.ui.page import *


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
        image (PIL.Image.Image):

    Returns:
        PIL.Image.Image:
    """
    if PLAYER_CHECK.match(image, offset=(30, 30)):
        return put_image_mask(image, mask='MASK_PLAYER')
    if MAIN_CHECK.match(image, offset=(30, 30)):
        return put_image_mask(image, mask='MASK_MAIN')

    return image
