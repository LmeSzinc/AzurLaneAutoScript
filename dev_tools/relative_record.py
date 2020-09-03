import os

from PIL import Image

import module.config.server as server

server.server = 'cn'  # Don't need to edit, it's used to avoid error.

from module.map_detection.view import View
from module.base.base import ModuleBase
from module.config.config import AzurLaneConfig
from module.base.utils import *


class Config:
    """
    Paste the config of map file here
    """
    ENABLE_GAME_STUCK_HANDLER = False
    pass


"""
Usage:
    Enter map, and find a siren.
    Manually count the siren is in which node, in local map view.
    Run relative_record.py first, to get enough images.
    Zoom-in one of those image, find an area where things don't rotate too much.
    Run relative_record_gif.py, to generate gif template file.
    Copy to assets/<server>/template
    Use new templates in config, like this:
        MAP_HAS_SIREN = True
        MAP_SIREN_TEMPLATE = ['U73', 'U81']

Arguments:
    CONFIG:     ini config file to load.
    FOLDER:     Folder to save.
    NAME:       Siren name, images will save in <FOLDER>/<NAME>
    NODE:       Node in local map view, that you are going to crop.
"""
CONFIG = 'alas'
FOLDER = ''
NAME = 'Deutschland'
NODE = 'D5'

for folder in [FOLDER, os.path.join(FOLDER, NAME)]:
    if not os.path.exists(folder):
        os.mkdir(folder)

cfg = AzurLaneConfig(CONFIG).merge(Config())
al = ModuleBase(cfg)
view = View(cfg)
al.device.screenshot()
view.load(al.device.image)
grid = view[node2location(NODE.upper())]

print('Please check if it is cropping the right area')
image = rgb2gray(grid.relative_crop((-0.5, -1, 0.5, 0), shape=(60, 60)))
image = Image.fromarray(image, mode='L').show()

images = []
for n in range(300):
    print(n)
    images.append(al.device.screenshot())
for n, image in enumerate(images):
    grid.image = np.array(image)
    image = rgb2gray(grid.relative_crop((-0.5, -1, 0.5, 0), shape=(60, 60)))
    image = Image.fromarray(image, mode='L')
    image.save(os.path.join(FOLDER, NAME, f'{n}.png'))
