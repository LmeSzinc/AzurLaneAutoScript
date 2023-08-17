from module.base.utils import area_pad, crop, rgb2gray
from module.research.assets import *

RESEARCH_SERIES = (SERIES_1, SERIES_2, SERIES_3, SERIES_4, SERIES_5)
RESEARCH_SCALING = [
    424 / 558,
    491 / 558,
    1.0,
    491 / 558,
    424 / 558,
]


def match_series(image, scaling):
    image = rgb2gray(image)

    if TEMPLATE_S6.match(image, scaling=scaling):
        return 6
    if TEMPLATE_S4_2.match(image, scaling=scaling):
        return 4
    if TEMPLATE_S4.match(image, scaling=scaling):
        return 4
    if TEMPLATE_S5.match(image, scaling=scaling):
        return 5
    if TEMPLATE_S3.match(image, scaling=scaling):
        return 3
    if TEMPLATE_S2.match(image, scaling=scaling):
        return 2
    if TEMPLATE_S1.match(image, scaling=scaling):
        return 1
    return 0


def get_research_series_3(image, series_button=RESEARCH_SERIES):
    """
    Args:
        image:
        series_button (list[Button]):

    Returns:
        list[int]:
    """
    return [
        match_series(crop(image, area_pad(button.area, pad=-10)), scaling)
        for scaling, button in zip(RESEARCH_SCALING, series_button)
    ]


def get_detail_series(image):
    """
    Args:
        image:

    Returns:
        int:
    """
    return match_series(crop(image, area_pad(SERIES_DETAIL.area, pad=-30)), scaling=1.0)
