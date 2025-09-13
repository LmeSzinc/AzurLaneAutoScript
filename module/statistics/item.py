import numpy as np

import module.config.server as server
from module.base.button import ButtonGrid
from module.base.utils import *
from module.logger import logger
from module.ocr.ocr import Digit, DigitYuv
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
# UI update in 20250814, but server TW is still old UI.
if server.server == 'tw':
    PRICE_OCR = DigitYuv([], letter=(255, 223, 57), threshold=128, name='Price_ocr')
elif server.server == 'jp':
    PRICE_OCR = Digit([], lang='cnocr', letter=(205, 205, 205), threshold=128, name='Price_ocr')
else:
    PRICE_OCR = Digit([], letter=(255, 255, 255), threshold=128, name='Price_ocr')


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
        image = crop(image, button.area)
        if image.shape == self.IMAGE_SHAPE:
            self.image = image
        else:
            self.image = cv2.resize(image, self.IMAGE_SHAPE, interpolation=cv2.INTER_CUBIC)
        self.is_valid = self.predict_valid()
        self._name = 'DefaultItem'
        self.amount = 1
        self._cost = 'DefaultCost'
        self.price = 0
        self.tag = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        """
        Args:
            value (str): Item name, such as 'PlateGeneralT3'. Suffix in name will be ignore.
                For example, 'Javelin' and 'Javelin_2' are different templates, but have same output name 'Javelin'.
        """
        if '_' in value:
            pre, suffix = value.rsplit('_', 1)
            if suffix.isdigit():
                value = pre
        self._name = value

    @property
    def cost(self):
        return self._cost

    @cost.setter
    def cost(self, value):
        if '_' in value:
            pre, suffix = value.rsplit('_', 1)
            if suffix.isdigit():
                value = pre
        self._cost = value

    def is_known_item(self):
        if self.name == 'DefaultItem':
            return False
        elif self.name.isdigit():
            return False
        else:
            return True

    def __str__(self):
        if self.name != 'DefaultItem' and self.cost == 'DefaultCost':
            name = f'{self.name}_x{self.amount}'
        elif self.name == 'DefaultItem' and self.cost != 'DefaultCost':
            name = f'{self.cost}_x{self.price}'
        else:
            name = f'{self.name}_x{self.amount}_{self.cost}_x{self.price}'

        if self.tag is not None:
            name = f'{name}_{self.tag}'

        return name

    def predict_valid(self):
        return np.mean(rgb2gray(self.image) > 127) > 0.1

    @property
    def button(self):
        return self._button.button

    def crop(self, area):
        return crop(self.image_raw, area_offset(area, offset=self._button.area[:2]))

    def __eq__(self, other):
        # For de-redundancy in Filter.apply()
        return str(self) == str(other)

    def __hash__(self):
        # For de-redundancy in merging two get items images
        return hash(self.name)


class ItemGrid:
    item_class = Item
    similarity = 0.92
    extract_similarity = 0.92
    cost_similarity = 0.75

    def __init__(self, grids, templates, template_area=(40, 21, 89, 70), amount_area=(60, 71, 91, 92),
                 cost_area=(6, 123, 84, 166), price_area=(52, 132, 132, 156), tag_area=(81, 4, 91, 8)):
        """
        Args:
            grids (ButtonGrid):
            templates (dict): Key: str, item_name, value: Template image.
            template_area (tuple):
            amount_area (tuple):
            cost_area (tuple):
            price_area (tuple):
            tag_area (tuple):
        """
        self.amount_ocr = AMOUNT_OCR
        self.price_ocr = PRICE_OCR
        self.grids = grids
        self.template_area = template_area
        self.amount_area = amount_area
        self.cost_area = cost_area
        self.price_area = price_area
        self.tag_area = tag_area

        self.colors = {}
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
            image (np.ndarray):
        """
        self.items = []
        for button in self.grids.buttons:
            item = self.item_class(image, button)
            if item.is_valid:
                self.items.append(item)

    def load_template_folder(self, folder):
        """
        Args:
            folder (str): Template folder.
        """
        logger.info(f'Loading template folder: {folder}')
        max_digit = 0
        data = load_folder(folder)
        for name, image in data.items():
            if name in self.templates:
                continue
            image = load_image(image)
            image = crop(image, area=self.template_area)
            self.colors[name] = cv2.mean(image)[:3]
            self.templates[name] = image
            self.templates_hit[name] = 0
            if name.isdigit():
                max_digit = max(max_digit, int(name))
            self.next_template_index += 1
        self.next_template_index = max(self.next_template_index, max_digit + 1)
        logger.attr('next_template_index', self.next_template_index)

    def load_cost_template_folder(self, folder):
        """
        Args:
            folder (str): Template folder.
        """
        max_digit = 0
        data = load_folder(folder)
        for name, image in data.items():
            if name in self.cost_templates:
                continue
            image = load_image(image)
            self.cost_templates[name] = image
            self.cost_templates_hit[name] = 0
            if name.isdigit():
                max_digit = max(max_digit, int(name))
            self.next_cost_template_index += 1
        self.next_cost_template_index = max(self.next_cost_template_index, max_digit + 1)

    def match_template(self, image, similarity=None):
        """
        Match templates, try most frequent hit templates first.

        Args:
            image (np.ndarray):
            similarity (float):

        Returns:
            str: Template name.
        """
        if similarity is None:
            similarity = self.similarity
        color = cv2.mean(crop(image, self.template_area))[:3]
        # Match frequently hit templates first
        names = np.array(list(self.templates.keys()))[np.argsort(list(self.templates_hit.values()))][::-1]
        # Match known templates first
        names = [name for name in names if not name.isdigit()] + [name for name in names if name.isdigit()]
        for name in names:
            if color_similar(color1=color, color2=self.colors[name], threshold=30):
                res = cv2.matchTemplate(image, self.templates[name], cv2.TM_CCOEFF_NORMED)
                _, sim, _, _ = cv2.minMaxLoc(res)
                if sim > similarity:
                    self.templates_hit[name] += 1
                    return name

        self.next_template_index += 1
        name = str(self.next_template_index)
        logger.info(f'New template: {name}')
        image = crop(image, self.template_area)
        self.colors[name] = cv2.mean(image)[:3]
        self.templates[name] = image
        self.templates_hit[name] = self.templates_hit.get(name, 0) + 1
        return name

    def extract_template(self, image, folder=None):
        """
        Args:
            image (np.ndarray):
            folder (str): Save templates if `folder` is provided

        Returns:
            dict: Newly found templates. Key: str, template name. Value: np.ndarray
        """
        self._load_image(image)
        prev = set(self.templates.keys())
        new = {}
        for item in self.items:
            name = self.match_template(item.image, similarity=self.extract_similarity)
            if name not in prev:
                new[name] = item.image
                # Rollback changes
                # self.next_template_index -= 1
                # del self.colors[name]
                # del self.templates[name]
                # del self.templates_hit[name]

        if folder is not None:
            for name, im in new.items():
                save_image(im, os.path.join(folder, f'{name}.png'))

        return new

    def match_cost_template(self, item):
        """
        Match templates, try most frequent hit templates first.

        Args:
            item (Item):

        Returns:
            str: Template name.
        """
        image = item.crop(self.cost_area)
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
        # self.cost_templates[name] = item.crop(self.cost_area)
        # self.cost_templates_hit[name] = self.cost_templates_hit.get(name, 0) + 1
        # return name

        # Not generating new cost template.
        # If not cost template matched, consider this item is empty.
        return None

    @staticmethod
    def predict_tag(image):
        """
        Args:
            image (np.ndarray): The tag_area of the item.
            Replace this method to predict tags.

        Returns:
            str: Tags are like `catchup`, `bonus`. Default to None
        """
        threshold = 50
        color = cv2.mean(np.array(image))[:3]
        if color_similar(color1=color, color2=(49, 125, 222), threshold=threshold):
            # Blue
            return 'catchup'
        elif color_similar(color1=color, color2=(33, 199, 239), threshold=threshold):
            # Cyan
            return 'bonus'
        elif color_similar(color1=color, color2=(255, 85, 41), threshold=threshold):
            # red
            return 'event'
        else:
            return None

    def predict(self, image, name=True, amount=True, cost=False, price=False, tag=False):
        """
        Args:
            image (np.ndarray):
            name (bool): If predict item name.
            amount (bool): If predict item amount.
            cost (bool): If predict the cost to buy item.
            price (bool): If predict item price.
            tag (bool): If predict item tag. Tags are like `catchup`, `bonus`.

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
        if tag:
            tag_list = [self.predict_tag(item.crop(self.tag_area)) for item in self.items]
            for item, t in zip(self.items, tag_list):
                item.tag = t

        # Delete wrong results
        items = [item for item in self.items if not (price and item.price <= 0)]
        diff = len(self.items) - len(items)
        if diff > 0:
            logger.warning(f'Ignore {diff} items, because price <= 0')
            self.items = items

        return self.items
