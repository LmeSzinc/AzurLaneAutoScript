import module.config.server as server

server.server = 'cn'  # Don't need to edit, it's used to avoid error.

import numpy as np
from PIL import Image

from module.config.config import AzurLaneConfig
from module.map_detection.view import View

"""
This file is use to debug a perspective error.
It will call the map detection module (module/map_detection/view.py), outside Alas.
"""


class Config:
    """
    Here are the default settings.
    """
    # Parameters for scipy.signal.find_peaks
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (150, 255 - 40),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 24, 255),
        'prominence': 10,
        'distance': 50,
        # 'width': (0, 7),
        'wlen': 1000
    }
    # Parameters for cv2.HoughLines
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 75
    EDGE_LINES_HOUGHLINES_THRESHOLD = 75
    # Parameters for lines pre-cleansing
    HORIZONTAL_LINES_THETA_THRESHOLD = 0.005
    VERTICAL_LINES_THETA_THRESHOLD = 18
    TRUST_EDGE_LINES = False  # True to use edge to crop inner, false to use inner to crop edge
    # Parameters for perspective calculating
    VANISH_POINT_RANGE = ((540, 740), (-3000, -1000))
    DISTANCE_POINT_X_RANGE = ((-3200, -1600),)
    # Parameters for line cleansing
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 3
    ERROR_LINES_TOLERANCE = (-10, 10)
    MID_DIFF_RANGE_H = (129 - 3, 129 + 3)
    MID_DIFF_RANGE_V = (129 - 3, 129 + 3)

    """
    Step 1:
        Paste your config here.
    """
    pass


"""
Step 2:
    Put your image here.
"""
file = ''
image = np.array(Image.open(file).convert('RGB'))


"""
Step 3:
    Choose one method, uncomment the code, run.
    There will be logs of local map view, and an image popup showing grid lines. Check if they are correct.
"""
# ==============================
# Method 1
# Perspective backend.
# ==============================
# cfg = Config()
# cfg.DETECTION_BACKEND = 'perspective'
# view = View(AzurLaneConfig('template').merge(cfg))
# view.load(image)
# view.predict()
# view.show()
# view.backend.draw()

# ==============================
# Method 2:
# Homography with real-time perspective calculation.
# This is the default method in Alas currently.
# ==============================
cfg = Config()
cfg.DETECTION_BACKEND = 'homography'
view = View(AzurLaneConfig('template').merge(cfg))
view.load(image)
view.predict()
view.show()
view.backend.draw()

# ==============================
# Method 3:
# Homography with hard-coded perspective data (HOMO_STORAGE).
# Get HOMO_STORAGE from log or from method 2.
# ==============================
# cfg = Config()
# cfg.DETECTION_BACKEND = 'homography'
# view = View(AzurLaneConfig('template').merge(cfg))
# homo_storage = ()  # Paste your HOMO_STORAGE here.
# view.backend.load_homography(storage=homo_storage)
# view.load(image)
# view.predict()
# view.show()
# view.backend.draw()
