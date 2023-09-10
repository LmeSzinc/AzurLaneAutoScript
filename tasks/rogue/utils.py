import re

from module.base.base import ModuleBase
from module.base.utils import area_offset
from module.ocr.ocr import OcrResultButton

REGEX_PUNCTUATION = re.compile(r'[ ,.\'"“”，。:：!！?？·•—/()（）「」『』【】《》]')


def parse_name(n):
    n = REGEX_PUNCTUATION.sub('', str(n)).lower()
    return n


def get_regex_from_keyword_name(keyword, attr_name):
    string = ""
    for instance in keyword.instances.values():
        if hasattr(instance, attr_name):
            for name in instance.__getattribute__(attr_name):
                string += f"{name}|"
    # some pattern contain each other, make sure each pattern end with "-" or the end of string
    return f"(?:({string[:-1]})(?:-|$))?"


def is_card_selected(main: ModuleBase, target: OcrResultButton, confirm_button):
    """
    There is a white border if a blessing is selected.
    For the enforce case, just check the confirm button turning to white
    """
    if not target:
        return main.image_color_count(confirm_button, (230, 230, 230))
    top_border = area_offset(target.area, (0, -180))
    return main.image_color_count(top_border, (255, 255, 255))
