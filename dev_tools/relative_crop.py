import os
import time

import module.config.server as server
from module.base.utils import *

server.server = 'cn'  # Don't need to edit, it's used to avoid error.

from module.config.config import AzurLaneConfig
from module.map_detection.view import View
from module.base.utils import load_image


class Config:
    """
    Paste the config of map file here
    """
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 17),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 17, 255),
        'prominence': 10,
        'distance': 50,
        'wlen': 1000
    }
    HOMO_EDGE_COLOR_RANGE = (0, 17)
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 210

from module.os.config import OSConfig
cfg = AzurLaneConfig('alas5').merge(Config())

# Folder to save temp images
folder = './screenshots/relative_crop'
# Put Screenshot here
file = r'E:\ProgramData\Pycharm\StarRailCopilot\screenshots\dev_screenshots\2023-12-22_00-41-21-728648.png'

i = load_image(file)
grids = View(cfg)
grids.load(np.array(i))
grids.predict()
grids.show()


os.makedirs(folder, exist_ok=True)
for grid in grids:
    # Find more relative_crop area in module/map/grid_predictor.py
    # This one is for `predict_enemy_genre`
    piece = rgb2gray(grid.relative_crop((-0, -0.2, 0.8, 0.2), shape=(40, 20)))

    file = '%s_%s_%s.png' % (int(time.time()), grid.location[0], grid.location[1])
    file = os.path.join(folder, file)
    Image.fromarray(piece).save(file)
