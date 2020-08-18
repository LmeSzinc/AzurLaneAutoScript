import os
import time

from PIL import Image

import module.config.server as server
from module.map_detection.utils import *

server.server = 'cn'  # Don't need to edit, it's used to avoid error.

from module.map_detection.view import View
from module.config.config import AzurLaneConfig


class Config:
    """
    Paste the config of map file here
    """
    pass


cfg = AzurLaneConfig().merge(Config())

# Folder to save temp images
folder = './screenshots/temp/'
# Put Screenshot here
file = './screenshots/TEMPLATE_AMBUSH_EVADE_FAILED.png'

i = Image.open(file).convert('RGB')
grids = View(cfg)
grids.load(np.array(i))
grids.predict()
grids.show()

for grid in grids:
    # Find more relative_crop area in module/map/grid_predictor.py
    # This one is for `predict_enemy_genre`
    piece = rgb2gray(grid.relative_crop((-0.5, -1, 0.5, 0), shape=(60, 60)))

    file = '%s_%s_%s.png' % (int(time.time()), grid.location[0], grid.location[1])
    file = os.path.join(folder, file)
    Image.fromarray(piece).save(file)
