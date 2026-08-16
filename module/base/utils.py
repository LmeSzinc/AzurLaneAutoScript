# Compatibility re-export layer (P1.1 refactor).
# All symbols moved to module/core/*; keep this module so existing
# `from module.base.utils import *` / explicit imports work unchanged.
# Module-level names (cv2/np/Image/re/random) are re-exported too, as
# 31 files import them from here (rope-expanded explicit imports).

import random

import re

import cv2
import numpy as np
from PIL import Image

from module.core.random import random_normal_distribution_int
from module.core.random import random_rectangle_point
from module.core.random import random_rectangle_vector
from module.core.random import random_rectangle_vector_opted
from module.core.random import random_line_segments
from module.core.random import ensure_time
from module.core.geometry import REGEX_NODE
from module.core.geometry import ensure_int
from module.core.geometry import area_offset
from module.core.geometry import area_pad
from module.core.geometry import limit_in
from module.core.geometry import area_limit
from module.core.geometry import area_size
from module.core.geometry import point_limit
from module.core.geometry import point_in_area
from module.core.geometry import area_in_area
from module.core.geometry import area_cross_area
from module.core.geometry import float2str
from module.core.geometry import point2str
from module.core.geometry import col2name
from module.core.geometry import name2col
from module.core.geometry import node2location
from module.core.geometry import location2node
from module.core.geometry import xywh2xyxy
from module.core.geometry import xyxy2xywh
from module.core.image import load_image
from module.core.image import save_image
from module.core.image import copy_image
from module.core.image import crop
from module.core.image import resize
from module.core.image import image_channel
from module.core.image import image_size
from module.core.image import image_paste
from module.core.image import rgb2gray
from module.core.image import rgb2hsv
from module.core.image import rgb2yuv
from module.core.image import rgb2luma
from module.core.image import get_bbox
from module.core.image import get_bbox_reversed
from module.core.image import extract_letters
from module.core.image import extract_white_letters
from module.core.image import color_mapping
from module.core.image import image_left_strip
from module.core.image import red_overlay_transparency
from module.core.image import ImageNotSupported
from module.core.color import get_color
from module.core.color import color_similarity
from module.core.color import color_similar
from module.core.color import color_similar_1d
from module.core.color import color_similarity_2d
from module.core.color import color_bar_percentage
