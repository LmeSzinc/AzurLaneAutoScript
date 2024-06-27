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
    pass

from module.os.config import OSConfig
cfg = AzurLaneConfig('alas').merge(OSConfig())

# Folder to save temp images
folder = './screenshots/relative_crop'
# Put Screenshot here
file = ''

i = load_image(file)
grids = View(cfg)
grids.load(np.array(i))
grids.predict()
grids.show()


os.makedirs(folder, exist_ok=True)
for grid in grids:
    # Find more relative_crop area in module/map/grid_predictor.py
    # This one is for `predict_enemy_genre`
    piece = rgb2gray(grid.relative_crop((-0.5, -1, 0.5, 0), shape=(60, 60)))

    file = '%s_%s_%s.png' % (int(time.time()), grid.location[0], grid.location[1])
    file = os.path.join(folder, file)
    Image.fromarray(piece).save(file)
