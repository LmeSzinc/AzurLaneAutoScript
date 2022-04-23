import os

import imageio
from PIL import Image
from tqdm import tqdm

import module.config.server as server

server.server = 'cn'  # Don't need to edit, it's used to avoid error.

from dev_tools.relative_record import FOLDER, NAME
from module.base.utils import *
from module.map_detection.utils import *

"""
Generate better siren template with brute-force.

Usage:
    See relative_record.py

Arguments:
    FOLDER:     Save folder from relative_record.
    NAME:       Siren name from relative_record.
                Save gif file to <FOLDER>/<NAME>_gif/<frame_count>_<average_similarity>_<size>.gif
    THRESHOLD:  If the similarity between a template and existing templates greater than THRESHOLD,
                this template will be dropped.
                Threshold in real detection is 0.85, for higher accuracy, threshold here should higher than 0.85.
    MAX_FRAME:  Maximum number of frames in gif.
"""
# Argument `FOLDER` import from relative_record.py by default. If you want to modify, change here.
# FOLDER = ''
# Argument `NAME` import from relative_record.py by default. If you want to modify, change here.
# NAME = 'Dace'
THRESHOLD = 0.92
MAX_FRAME = 6


def crop(image, area):
    """Crop image like pillow, when using opencv / numpy

    Args:
        image (np.ndarray):
        area:

    Returns:
        np.ndarray:
    """
    x1, y1, x2, y2 = area
    return image[y1:y2, x1:x2]


class RelativeRecord:
    def __init__(self):
        self.images = [np.array(Image.open(os.path.join(FOLDER, NAME, file)).convert('RGB')) for file in
                       os.listdir(os.path.join(FOLDER, NAME))
                       if file[-4:] == '.png']
        self.images = np.array(self.images)
        self.images_amount = len(self.images)
        self.folder = os.path.join(FOLDER, f'{NAME}_gif')
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)

    def count(self, area):
        mask = np.full(self.images_amount, False, dtype=bool)

        template = crop(self.images[0], area=area)
        template_0 = template
        count = 0

        while np.sum(mask) < self.images_amount and count < MAX_FRAME:
            count += 1
            mask_inv = mask == False
            m = [np.max(cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)) > THRESHOLD
                 for image in self.images[mask_inv]]

            mask[mask_inv] |= m

            image = self.images[np.argmin(mask)]
            res = cv2.matchTemplate(image, template_0, cv2.TM_CCOEFF_NORMED)
            _, sim, _, loca = cv2.minMaxLoc(res)
            template = crop(image, area=area_offset(area, np.subtract(loca, area[:2])))

        return count

    def count_by_size(self, size, padding=10):
        image_size = self.images[0].shape
        stats = set()
        print('Trying templates in 2x2 grid')
        area_list = [(x, y, x + size[0], y + size[1])
                     for x in range(padding, image_size[0] - size[0] - padding, 2)
                     for y in range(padding, image_size[1] - size[1] - padding, 2)]
        for area in tqdm(area_list):
                count = self.count(area)
                if count < MAX_FRAME:
                    stats.add(area)

        print('Generating all template area')
        offset_list = np.array([(1, 0, 1, 0), (-1, 0, -1, 0), (0, 1, 0, 1), (0, -1, 0, -1)])
        out = stats.copy()
        visited = set()
        for area in tqdm(stats):
            area = np.array(area)
            for offset in offset_list:
                new = area + offset
                new = tuple(new.tolist())
                if new not in visited and self.count(area=new) < MAX_FRAME:
                    out.add(new)
                visited.add(new)

        return out

    def get_gif(self, area):
        templates = [crop(self.images[0], area=area)]
        sim_list = []
        for n, image in enumerate(self.images):
            max_sim = 0
            max_loca = (0, 0)
            for template in templates:
                res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
                _, sim, _, loca = cv2.minMaxLoc(res)
                if sim > max_sim:
                    max_sim = sim
                    max_loca = loca

            if max_sim > THRESHOLD:
                sim_list.append(max_sim)
                continue

            templates.append(crop(image, area=area_offset(area, np.subtract(max_loca, area[:2]))))

        return np.mean(sim_list), templates

    def run_by_size(self, size):
        sim_dict = {}
        template_dict = {}
        area_list = self.count_by_size(size)
        print('Trying all templates')
        for area in tqdm(area_list):
            sim, templates = self.get_gif(area)
            count = len(templates)

            if sim > sim_dict.get(count, 0):
                sim_dict[count] = sim
                template_dict[count] = templates

        print('Saving gif')
        for count, sim, templates in zip(sim_dict.keys(), sim_dict.values(), template_dict.values()):
            sim = str(int((1 - sim) * 1000000)).rjust(6, '0')
            name = f'{count}_{sim}_{"-".join([str(x) for x in size])}'
            imageio.mimsave(os.path.join(self.folder, f'{name}.gif'), templates, fps=3)
        print(f'{size} done')


r = RelativeRecord()
r.run_by_size((15, 18))
print('relative_record_gif2 done')
