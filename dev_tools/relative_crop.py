import os
from PIL import Image
import time
# os.chdir('../')
print(os.getcwd())
import module.config.server as server

server.server = 'cn'  # Don't need to edit, it's used to avoid error.

from module.map.grids import Grids
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
grids = Grids(i, cfg)
grids.predict()
grids.show()

for grid in grids:
    # Find more relative_crop area in module/map/grid_predictor.py
    # This one is for `predict_enemy_genre`
    piece = grid.get_relative_image((-1, -1, 1, 0), output_shape=(120, 60))

    file = '%s_%s_%s.png' % (int(time.time()), grid.location[0], grid.location[1])
    file = os.path.join(folder, file)
    piece.save(file)
