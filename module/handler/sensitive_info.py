import re

from module.base.mask import Mask
from module.ui.assets import PLAYER_CHECK
from module.ui.page import MAIN_GOTO_CAMPAIGN_WHITE, MAIN_GOTO_FLEET

MASK_MAIN = Mask('./assets/mask/MASK_MAIN.png')
MASK_MAIN_WHITE = Mask('./assets/mask/MASK_MAIN_WHITE.png')
MASK_PLAYER = Mask('./assets/mask/MASK_PLAYER.png')


def handle_sensitive_image(image):
    """
    Args:
        image:

    Returns:
        np.ndarray:
    """
    if PLAYER_CHECK.match(image, offset=(30, 30)):
        image = MASK_PLAYER.apply(image)
    if MAIN_GOTO_FLEET.match(image, offset=(30, 30)):
        image = MASK_MAIN.apply(image)
    if MAIN_GOTO_CAMPAIGN_WHITE.match(image, offset=(30, 30)):
        image = MASK_MAIN_WHITE.apply(image)

    return image


def handle_sensitive_text(text):
    """
    Args:
        text (str):

    Returns:
        str:
    """
    text = re.sub('File \"(.*?)AzurLaneAutoScript', 'File \"C:\\\\fakepath\\\\AzurLaneAutoScript', text)
    text = re.sub('\[Adb_binary\] (.*?)AzurLaneAutoScript', '[Adb_binary] C:\\\\fakepath\\\\AzurLaneAutoScript', text)
    return text


def handle_sensitive_logs(logs):
    return [handle_sensitive_text(line) for line in logs]
