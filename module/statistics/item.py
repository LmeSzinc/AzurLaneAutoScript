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


AMOUNT_OCR = AmountOcr([], threshold=96, name='Amount_ocr')
PRICE_OCR = Digit([], letter=(255, 223, 57), threshold=32, name='Price_ocr')


class Item:
    IMAGE_SHAPE = (96, 96)

    def __init__(self, image, button):
        """
        Args:
            image:
            button:
        """
        self.image_raw = image
        self._button = button
        image = np.array(image.crop(button.area))
        if image.shape == self.IMAGE_SHAPE:
            self.image = image
        else:
            self.image = cv2.resize(image, self.IMAGE_SHAPE, interpolation=cv2.INTER_CUBIC)
        self.is_valid = np.mean(rgb2gray(self.image) > 127) > 0.1
        self._name = 'DefaultItem'
        self.amount = 1
        self.cost = 'DefaultCost'
        self.price = 0

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
        if self.name != 'DefaultItem' and self.cost == 'DefaultCost':
            return f'{self.name}_x{self.amount}'
        elif self.name == 'DefaultItem' and self.cost != 'DefaultCost':
            return f'{self.cost}_x{self.price}'
        else:
            return f'{self.name}_x{self.amount}_{self.cost}_x{self.price}'

    @property
    def button(self):
        return self._button.button

    def crop(self, area):
        return self.image_raw.crop(area_offset(area, offset=self._button.area[:2]))


class ItemGrid:
    similarity = 0.92
    cost_similarity = 0.75

    def __init__(self, grids, templates, template_area=(40, 21, 89, 70), amount_area=(60, 71, 91, 92),
                 cost_area=(6, 123, 84, 166), price_area=(52, 132, 132, 156)):
        """
        Args:
            grids (ButtonGrid):
            templates (dict): Key: str, item_name, value: Template image.
            template_area (tuple):
            amount_area (tuple):
            cost_area (tuple):
            price_area (tuple):
        """
        self.amount_ocr = AMOUNT_OCR
        self.price_ocr = PRICE_OCR
        self.grids = grids
        self.template_area = template_area
        self.amount_area = amount_area
        self.cost_area = cost_area
        self.price_area = price_area

        self.templates = {}
        self.templates_hit = {}
        self.next_template_index = len(self.templates.keys())
        for name, template in templates.items():
            self.templates[name] = crop(template.image, area=self.template_area)
            self.templates_hit[name] = 0
            if name.isdigit() and int(name) > self.next_template_index:
                self.next_template_index = int(name)

        self.cost_templates = {}
        self.cost_templates_hit = {}
        self.next_cost_template_index = len(self.cost_templates.keys())

        self.items = []

    def _load_image(self, image):
        """
        Args:
            image: Pillow image
        """
        self.items = []
        for button in self.grids.buttons():
            item = Item(image, button)
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

    def load_cost_template_folder(self, folder):
        """
        Args:
            folder (str): Template folder.
        """
        data = load_folder(folder)
        for name, image in data.items():
            if name in self.cost_templates:
                continue
            image = load_image(image)
            self.cost_templates[name] = np.array(image)
            self.cost_templates_hit[name] = 0
            self.next_cost_template_index += 1

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

    def match_cost_template(self, item):
        """
        Match templates, try most frequent hit templates first.

        Args:
            item (Item):

        Returns:
            str: Template name.
        """
        image = np.array(item.crop(self.cost_area))
        names = np.array(list(self.cost_templates.keys()))[np.argsort(list(self.cost_templates_hit.values()))][::-1]
        for name in names:
            res = cv2.matchTemplate(image, self.cost_templates[name], cv2.TM_CCOEFF_NORMED)
            _, similarity, _, _ = cv2.minMaxLoc(res)
            if similarity > self.cost_similarity:
                self.cost_templates_hit[name] += 1
                return name

        # self.next_cost_template_index += 1
        # name = str(self.next_cost_template_index)
        # logger.info(f'New template: {name}')
        # self.cost_templates[name] = np.array(item.crop(self.cost_area))
        # self.cost_templates_hit[name] = self.cost_templates_hit.get(name, 0) + 1
        # return name

        # Not generating new cost template.
        # If not cost template matched, consider this item is empty.
        return None

    def predict(self, image, name=True, amount=True, cost=False, price=False):
        """
        Args:
            image: Pillow image
            name (bool): If predict item name.
            amount (bool): If predict item amount.
            cost (bool): If predict the cost to buy item.
            price (bool): If predict item price.

        Returns:
            list[Item]:
        """
        self._load_image(image)
        if amount:
            amount_list = [item.crop(self.amount_area) for item in self.items]
            amount_list = self.amount_ocr.ocr(amount_list, direct_ocr=True)
            for item, a in zip(self.items, amount_list):
                item.amount = a
        if name:
            name_list = [self.match_template(item.image) for item in self.items]
            for item, n in zip(self.items, name_list):
                item.name = n
        if cost:
            cost_list = [self.match_cost_template(item) for item in self.items]
            self.items = [item for item, c in zip(self.items, cost_list) if c is not None]
            cost_list = [c for c in cost_list if c is not None]
            for item, c in zip(self.items, cost_list):
                item.cost = c
        if price and len(self.items):
            price_list = [item.crop(self.price_area) for item in self.items]
            price_list = self.price_ocr.ocr(price_list, direct_ocr=True)
            for item, p in zip(self.items, price_list):
                item.price = p

        # Delete wrong results
        items = [item for item in self.items if not (price and item.price <= 0)]
        diff = len(self.items) - len(items)
        if diff > 0:
            logger.warning(f'Ignore {diff} items, because price <= 0')
            self.items = items

        return self.items
