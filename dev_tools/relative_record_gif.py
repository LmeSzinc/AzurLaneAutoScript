import os

import imageio
from PIL import Image

import module.config.server as server

server.server = 'cn'  # Don't need to edit, it's used to avoid error.

from module.base.utils import *
from module.map_detection.utils import *

"""
Usage:
    See relative_record.py

Arguments:
    FOLDER:     The same folder used in relative_record.
    NAME:       Siren name. Load images in <FOLDER>/<NAME>
                Save gif file to <FOLDER>/TEMPLATE_SIREN_<NAME>.gif
    AREA:       Area to crop, such as (32, 32, 54, 52).
                Choose an area where things don't rotate too much.
    THRESHOLD:  If the similarity between a template and existing templates greater than THRESHOLD,
                this template will be dropped.
                Threshold in real detection is 0.85, for higher accuracy, threshold here should higher than 0.85.
"""
FOLDER = ''
NAME = 'Deutschland'
AREA = (32, 32, 54, 52)
THRESHOLD = 0.90

images = [np.array(Image.open(os.path.join(FOLDER, NAME, file))) for file in os.listdir(os.path.join(FOLDER, NAME)) if file[-4:] == '.png']
templates = [crop(images[0], area=AREA)]


def matched(im):
    for template in templates:
        res = cv2.matchTemplate(im, template, cv2.TM_CCOEFF_NORMED)
        _, sim, _, _ = cv2.minMaxLoc(res)
        if sim > THRESHOLD:
            return True

    return False


for n, image in enumerate(images):
    if matched(image):
        continue
    print(f'New template: {n}')
    templates.append(crop(image, area=AREA))

imageio.mimsave(os.path.join(FOLDER, f'TEMPLATE_SIREN_{NAME}.gif'), templates, fps=3)
