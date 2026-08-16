# Compatibility re-export layer (P1.1 refactor).
# All symbols moved to module/core/*; keep this module so existing
# `from module.base.utils import *` / explicit imports work unchanged.
# Module-level names (cv2/np/Image/re/random) are re-exported too, as
# 31 files import them from here (rope-expanded explicit imports).
# `__all__` keeps ruff F401 --fix from deleting these re-exports
# (see commit 704dcb483 for the original incident).

import random
import re

import cv2
import numpy as np
from PIL import Image

from module.core.color import (
    color_bar_percentage,
    color_similar,
    color_similar_1d,
    color_similarity,
    color_similarity_2d,
    get_color,
)
from module.core.geometry import (
    REGEX_NODE,
    area_cross_area,
    area_in_area,
    area_limit,
    area_offset,
    area_pad,
    area_size,
    col2name,
    ensure_int,
    float2str,
    limit_in,
    location2node,
    name2col,
    node2location,
    point2str,
    point_in_area,
    point_limit,
    xywh2xyxy,
    xyxy2xywh,
)
from module.core.image import (
    ImageNotSupported,
    color_mapping,
    copy_image,
    crop,
    extract_letters,
    extract_white_letters,
    get_bbox,
    get_bbox_reversed,
    image_channel,
    image_left_strip,
    image_paste,
    image_size,
    load_image,
    red_overlay_transparency,
    resize,
    rgb2gray,
    rgb2hsv,
    rgb2luma,
    rgb2yuv,
    save_image,
)
from module.core.random import (
    ensure_time,
    random_line_segments,
    random_normal_distribution_int,
    random_rectangle_point,
    random_rectangle_vector,
    random_rectangle_vector_opted,
)

__all__ = [
    "REGEX_NODE",
    "Image",
    "ImageNotSupported",
    "area_cross_area",
    "area_in_area",
    "area_limit",
    "area_offset",
    "area_pad",
    "area_size",
    "col2name",
    "color_bar_percentage",
    "color_mapping",
    "color_similar",
    "color_similar_1d",
    "color_similarity",
    "color_similarity_2d",
    "copy_image",
    "crop",
    "cv2",
    "ensure_int",
    "ensure_time",
    "extract_letters",
    "extract_white_letters",
    "float2str",
    "get_bbox",
    "get_bbox_reversed",
    "get_color",
    "image_channel",
    "image_left_strip",
    "image_paste",
    "image_size",
    "limit_in",
    "load_image",
    "location2node",
    "name2col",
    "node2location",
    "np",
    "point2str",
    "point_in_area",
    "point_limit",
    "random",
    "random_line_segments",
    "random_normal_distribution_int",
    "random_rectangle_point",
    "random_rectangle_vector",
    "random_rectangle_vector_opted",
    "re",
    "red_overlay_transparency",
    "resize",
    "rgb2gray",
    "rgb2hsv",
    "rgb2luma",
    "rgb2yuv",
    "save_image",
    "xywh2xyxy",
    "xyxy2xywh",
]
