import cv2
import numpy as np

from module.base.utils import color_similar
from module.logger import logger
from module.ocr.ocr import Digit, Ocr
from module.statistics.item import Item, ItemGrid


class CounterOcr(Ocr):
    def __init__(self, buttons, lang='azur_lane',
                 letter=(255, 255, 255),
                 threshold=128,
                 alphabet='0123456789/IDSB@OQZl]i',
                 name=None):
        super().__init__(buttons, lang=lang, letter=letter, threshold=threshold, alphabet=alphabet, name=name)

    def pre_process(self, image):
        image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        # add contrast to the image for better ocr results
        cv2.convertScaleAbs(image, alpha=1.5, beta=-64, dst=image)
        return image

    def after_process(self, result):
        # print(result)
        result = super().after_process(result)
        result = result.replace('I', '1').replace('D', '0').replace('S', '5')
        result = result.replace('B', '8').replace('Z', '2')
        result = result.replace('@', '0').replace('O', '0').replace('Q', '0')
        result = result.replace('l', '1').replace(']', '1').replace('i', '1')
        return result

    def ocr(self, image, direct_ocr=False):
        """
        Do OCR on a counter, such as `14/15`, and returns 14, 15

        Args:
            image:
            direct_ocr:

        Returns:
            list[list[int]: [[current, total]].
        """
        result = super().ocr(image, direct_ocr=direct_ocr)
        # if something goes wrong here, for example '/1',
        # falls back to 1/1.
        if isinstance(result, list):
            result_list = []
            for i in result:
                try:
                    current, total = [int(j) for j in i.split('/')]
                    result_list.append([current, total])
                except ValueError:
                    logger.warning(f'Ocr result {i} is revised to 1/1')
                    result_list.append([1, 1])
            return result_list
        else:
            try:
                current, total = [int(i) for i in result.split('/')]
            except ValueError:
                logger.warning(f'Ocr result {result} is revised to 1/1')
                current = 1
                total = 1
            finally:
                return [current, total]

COUNTER_OCR = CounterOcr([], lang='cnocr', name='Counter_ocr')


class EventShopItem(Item):
    # mainly used to distinguish equip skin box and event equip
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._scroll_pos = None
        self.total_count = 1
        self.count = 1

    @property
    def scroll_pos(self):
        return self._scroll_pos

    @scroll_pos.setter
    def scroll_pos(self, value):
        self._scroll_pos = value

    def __str__(self):
        if self.name != 'DefaultItem' and self.cost == 'DefaultCost':
            name = f'{self.name}_x{self.amount}'
        elif self.name == 'DefaultItem' and self.cost != 'DefaultCost':
            name = f'{self.cost}_x{self.price}'
        elif self.name.isdigit():
            name = f'{self.name}_{self.count}/{self.total_count}_{self.cost}_x{self.price}'
        else:
            name = f'{self.name}_x{self.amount}_{self.cost}_x{self.price}'

        if self.tag is not None:
            name = f'{name}_{self.tag}'

        return name

    def __eq__(self, other):
        return id(self) == id(other)

    def identify_name(self):
        if not self.name.isdigit():
            return
        elif self.price == 8000 and self.cost == "Pt":
            self.name = "ShipSSR"
        elif self.price in [200, 300] and self.cost == "URPt":
            self.name = "ShipUR"
        elif self.price == 2000 and self.cost == "Pt":
            if self.total_count == 4:
                self.name = "Meta"
            elif self.total_count == 10:
                self.name = "SkinBox"
            elif self.total_count == 1:
                self.name = "EquipSSR"
        elif self.price == 10000 and self.cost == "URPt":
            self.name = "EquipUR"
        elif self.price == 150 and self.cost == "Pt" and self.total_count == 500:
            self.name = "PtUR"
        else:
            if self.cost == "Pt":
                self.name = "EquipSSR"
            elif self.cost == "URPt":
                self.name = "EquipUR"


class EventShopItemGrid(ItemGrid):
    item_class = EventShopItem
    cost_similarity = 0.5
    # similarity = 0.95
    extract_similarity = 0.95

    def __init__(self, grids, templates, template_area=(40, 21, 89, 70), amount_area=(60, 71, 96, 97),
                 cost_area=(6, 123, 84, 166), price_area=(52, 132, 132, 156), tag_area=(0, 74, 1, 92),
                 counter_area=(80, 170, 138, 190)):
        super().__init__(grids, templates, template_area, amount_area, cost_area, price_area, tag_area)
        self.counter_ocr = COUNTER_OCR
        self.counter_area = counter_area

    def match_cost_template(self, item):
        """
        Overwrite ItemGrid.match_cost_template.

        Returns:
            str: Template name = 'Pt' or 'URPt'.
        """
        image = item.crop(self.cost_area)
        names = np.array(list(self.cost_templates.keys()))[np.argsort(list(self.cost_templates_hit.values()))][::-1]
        for name in names:
            if not name in ["Pt", "URPt"]:
                continue

            res = cv2.matchTemplate(image, self.cost_templates[name], cv2.TM_CCOEFF_NORMED)
            _, similarity, _, _ = cv2.minMaxLoc(res)
            if similarity > self.cost_similarity:
                self.cost_templates_hit[name] += 1
                return name

        return None

    @staticmethod
    def predict_tag(image):
        """
        Args:
            image (np.ndarray): The tag_area of the item.

        Returns:
            str: Tags are like `unobtained`. Default to None
        """
        threshold = 50
        color = cv2.mean(np.array(image))[:3]
        if color_similar(color1=color, color2=(255, 89, 90), threshold=threshold):
            # red
            return 'unobtained'
        else:
            return None

    def predict(self, image, counter=True, scroll_pos=None):
        super().predict(image, name=True, amount=True, cost=True, price=True, tag=True)

        # temporary code to distinguish between DR and PR. Shit code.
        for item in self.items:
            if item.name.startswith('DR') and item.price == 500:
                item.name = 'P' + item.name[1:]
            if item.name.startswith('PR') and item.price == 1000:
                item.name = 'D' + item.name[1:]

        if counter and len(self.items):
            counter_list = [item.crop(self.counter_area) for item in self.items]
            counter_list = self.counter_ocr.ocr(counter_list, direct_ocr=True)
            for i, t in zip(self.items, counter_list):
                i.count, i.total_count = t

        if isinstance(scroll_pos, float) and len(self.items):
            for i in self.items:
                i.scroll_pos = scroll_pos

        for item in self.items:
            item.identify_name()

        return self.items
