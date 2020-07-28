import collections

import numpy as np

from module.base.decorator import Config
from module.base.utils import extract_letters, area_offset
from module.exception import CampaignNameError
from module.logger import logger
from module.ocr.ocr import Ocr
from module.template.assets import TEMPLATE_STAGE_CLEAR, TEMPLATE_STAGE_PERCENT, Button


def ensure_chapter_index(name):
    """
    Args:
        name (str, int):

    Returns:
        int
    """
    if isinstance(name, int):
        return name
    else:
        if name.isdigit():
            return int(name)
        elif name in ['a', 'c', 'sp', 'ex_sp']:
            return 1
        elif name in ['b', 'd']:
            return 2


def ocr_result_process(result):
    # The result will be like '7--2', because tha dash in game is '–' not '-'
    result = result.lower().replace('--', '-').replace('--', '-')
    if result.startswith('-'):
        result = result[1:]
    if len(result) == 2 and result[0].isdigit():
        result = '-'.join(result)
    return result


def separate_name(name):
    """
    Args:
        name (str): Stage name in lowercase, such as 7-2, d3, sp3.

    Returns:
        tuple[str]: Campaign_name and stage index in lowercase, Such as ['7', '2'], ['d', '3'], ['sp', '3'].
    """
    if name == 'sp':
        return 'ex_sp', '1'
    elif '-' in name:
        return name.split('-')
    elif name.startswith('sp'):
        return 'sp', name[-1]
    elif name[0] in 'abcdef':
        return name[0], name[-1]

    logger.warning(f'Unknown stage name: {name}')
    return name[0], name[1:]


class CampaignOcr:
    stage_entrance = {}
    campaign_chapter = 0

    def campaign_match_multi(self, template, image, name_offset=(75, 9), name_size=(60, 16),
                             name_letter=(255, 255, 255), name_thresh=128):
        """
        Args:
            template (Template):
            image: Screenshot
            name_offset (tuple[int]):
            name_size (tuple[int]):
            name_letter (tuple[int]):
            name_thresh (int):

        Returns:
            list[Button]: Stage clear buttons.
        """
        digits = []
        color = tuple(np.mean(np.mean(template.image, axis=0), axis=0))
        result = template.match_multi(image, similarity=0.95)

        for point in result:
            point = point[::-1]
            button = tuple(np.append(point, point + template.image.shape[:2][::-1]))
            point = point + name_offset
            name = image.crop(np.append(point, point + name_size))
            name = extract_letters(name, letter=name_letter, threshold=name_thresh)
            stage = self._extract_stage_name(name)
            digits.append(
                Button(area=area_offset(stage, point), color=color, button=button, name='stage'))

        return digits

    @Config.when(SERVER='en')
    def campaign_extract_name_image(self, image):
        digits = []
        digits += self.campaign_match_multi(TEMPLATE_STAGE_CLEAR, image, name_offset=(70, 12), name_size=(60, 14))
        digits += self.campaign_match_multi(TEMPLATE_STAGE_PERCENT, image, name_offset=(45, 3), name_size=(60, 14))

        if len(digits) == 0:
            logger.warning('No stage found.')

        return digits

    @Config.when(SERVER=None)
    def campaign_extract_name_image(self, image):
        digits = []
        digits += self.campaign_match_multi(TEMPLATE_STAGE_CLEAR, image, name_offset=(75, 9), name_size=(60, 16))
        digits += self.campaign_match_multi(TEMPLATE_STAGE_PERCENT, image, name_offset=(48, 0), name_size=(60, 16))

        if len(digits) == 0:
            logger.warning('No stage found.')

        return digits

    @staticmethod
    def _extract_stage_name(image):
        x_skip = 10
        interval = 5
        x_color = np.convolve(np.mean(image, axis=0), np.ones(interval), 'valid') / interval
        x_list = np.where(x_color[x_skip:] > 235)[0]
        if x_list is None or len(x_list) == 0:
            logger.warning('No interval between digit and text.')

        area = (0, 0, x_list[0] + 1 + x_skip, image.shape[0])
        return np.array(area) + (-3, -7, 3, 7)

    @staticmethod
    def _name_separate(image):
        """
        Args:
            image (np.ndarray): (height, width)

        Returns:
            list[np.ndarray]:
        """
        # Image.fromarray(image.astype('uint8'), mode='L').show()
        x_skip = 2
        interval = 5
        x_color = np.convolve(np.mean(image, axis=0), np.ones(interval), 'valid') / interval
        x_list = np.where(x_color[x_skip:] > 235)[0]
        if x_list is None or len(x_list) == 0:
            logger.warning('No interval between digit and text.')
        image = image[:, :x_list[0] + 1 + x_skip]

        dash_color_range = (220 - 3, 220 + 3)
        dash_height_index = 9
        mean = np.mean(image, axis=0)
        # print(mean)
        x_list = np.where(
            (mean > dash_color_range[0])
            & (mean < dash_color_range[1])
            & (np.argmin(image, axis=0) == dash_height_index)
        )[0]
        if x_list is None or len(x_list) == 0:
            logger.warning('No dash found between digits')
        chapter = (0, 0, x_list[0] - 1, image.shape[0])
        stage = (x_list[-1] + 1, 0, image.shape[1], image.shape[0])

        return chapter, stage

    def _get_stage_name(self, image):
        self.stage_entrance = {}
        buttons = self.campaign_extract_name_image(image)

        ocr = Ocr(buttons, name='campaign', letter=(255, 255, 255), threshold=128, alphabet='0123456789ABCDEFSP-')
        result = ocr.ocr(image)
        if not isinstance(result, list):
            result = [result]
        result = [ocr_result_process(res) for res in result]

        chapter = [separate_name(res)[0] for res in result]
        counter = collections.Counter(chapter)
        self.campaign_chapter = counter.most_common()[0][0]

        for name, button in zip(result, buttons):
            button.area = button.button
            button.name = name
            self.stage_entrance[name] = button

        logger.attr('Chapter', self.campaign_chapter)
        logger.attr('Stage', ', '.join(self.stage_entrance.keys()))

    def get_chapter_index(self, image):
        """
        A tricky method for ui_ensure_index
        """
        try:
            self._get_stage_name(image)
        except IndexError:
            raise CampaignNameError

        return ensure_chapter_index(self.campaign_chapter)
