import numpy as np

from module.base.button import ButtonGrid
from module.base.utils import *
from module.logger import logger
from module.ocr.ocr import Digit
from module.statistics.utils import *


class AmountOcr(Digit):
    def pre_process(self, image):
        """
        Args:
            image (np.ndarray): Shape (height, width, channel)

        Returns:
            np.ndarray: Shape (width, height)
        """
        image = extract_white_letters(image, threshold=self.threshold)
        return image.astype(np.uint8)


AMOUNT_OCR = AmountOcr([], threshold=64, name='Amount_ocr')


class Item:
    IMAGE_SHAPE = (96, 96)

    def __init__(self, image):
        """
        Args:
            image:
        """
        image = np.array(image)
        if image.shape == self.IMAGE_SHAPE:
            self.image = image
        else:
            self.image = cv2.resize(image, self.IMAGE_SHAPE, interpolation=cv2.INTER_CUBIC)
        self.is_valid = np.mean(rgb2gray(self.image) > 127) > 0.1
        self._name = 'DefaultItem'
        self.amount = 1

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        """
        Args:
            value (str): Item name, Camel-Case, such as 'PlateGeneralT3'. Suffix in name will be ignore.
                For example, 'Javelin' and 'Javelin_2' are different templates, but have same output name 'Javelin'.
        """
        if '_' in value:
            value = value.split('_')[0]
        self._name = value

    def __str__(self):
        return f'{self.name}_x{self.amount}'


class ItemGrid:
    similarity = 0.92

    def __init__(self, grids, templates, template_area=(40, 21, 89, 70), amount_area=(60, 71, 91, 92)):
        """
        Args:
            grids (ButtonGrid):
            templates (dict): Key: str, item_name, value: Template image.
            template_area (tuple):
            amount_area (tuple):
        """
        self.amount_ocr = AMOUNT_OCR
        self.grids = grids
        self.template_area = template_area
        self.amount_area = amount_area
        self.templates = {}
        self.templates_hit = {}
        self.next_template_index = len(self.templates.keys())
        for name, template in templates.items():
            self.templates[name] = crop(template.image, area=self.template_area)
            self.templates_hit[name] = 0
            if name.isdigit() and int(name) > self.next_template_index:
                self.next_template_index = int(name)

        self.items = []

    def _load_image(self, image):
        """
        Args:
            image: Pillow image
        """
        self.items = []
        for button in self.grids.buttons():
            item = Item(image.crop(button.area))
            if item.is_valid:
                self.items.append(item)

    def load_template_folder(self, folder):
        """
        Args:
            folder (str): Template folder.
        """
        data = load_folder(folder)
        for name, image in data.items():
            if name in self.templates:
                continue
            image = load_image(image)
            self.templates[name] = crop(np.array(image), area=self.template_area)
            self.templates_hit[name] = 0
            self.next_template_index += 1

    def match_template(self, image):
        """
        Match templates, try most frequent hit templates first.

        Args:
            image:

        Returns:
            str: Template name.
        """
        image = np.array(image)
        names = np.array(list(self.templates.keys()))[np.argsort(list(self.templates_hit.values()))][::-1]
        for name in names:
            res = cv2.matchTemplate(image, self.templates[name], cv2.TM_CCOEFF_NORMED)
            _, similarity, _, _ = cv2.minMaxLoc(res)
            if similarity > self.similarity:
                self.templates_hit[name] += 1
                return name

        self.next_template_index += 1
        name = str(self.next_template_index)
        logger.info(f'New template: {name}')
        self.templates[name] = crop(image, self.template_area)
        self.templates_hit[name] = self.templates_hit.get(name, 0) + 1
        return name

    def extract_template(self, image):
        """
        Args:
            image: Pillow image

        Returns:
            dict: Newly found templates. Key: str, template name. Value: pillow image
        """
        self._load_image(image)
        prev = set(self.templates.keys())
        new = {}
        for item in self.items:
            name = self.match_template(item.image)
            if name not in prev:
                new[name] = Image.fromarray(item.image)

        return new

    def predict(self, image):
        """
        Args:
            image: Pillow image

        Returns:
            list[Item]:
        """
        self._load_image(image)
        amount = [crop(item.image, area=self.amount_area) for item in self.items]
        amount = self.amount_ocr.ocr(amount, direct_ocr=True)
        name = [self.match_template(item.image) for item in self.items]
        for item, a, n in zip(self.items, amount, name):
            item.amount = a
            item.name = n

        return self.items
