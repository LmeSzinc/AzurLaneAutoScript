import collections

import numpy as np

from module.base.ocr import Ocr
from module.base.utils import extract_letters, area_offset
from module.logger import logger
from module.template.assets import TEMPLATE_STAGE_CLEAR, TEMPLATE_STAGE_PERCENT, Button
from module.exception import CampaignNameError

stage_clear_color = tuple(np.mean(np.mean(TEMPLATE_STAGE_CLEAR.image, axis=0), axis=0))
stage_percentage_color = tuple(np.mean(np.mean(TEMPLATE_STAGE_PERCENT.image, axis=0), axis=0))


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
        elif name in ['a', 'c', 'sp']:
            return 1
        elif name in ['b', 'd']:
            return 2


def ocr_result_process(result):
    result = result.lower().replace('--', '-')
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
    if '-' in name:
        return name.split('-')
    elif name.startswith('sp'):
        return 'sp', name[-1]
    elif name[0] in 'abcdef':
        return name[0], name[-1]

    logger.warning(f'Unknown stage name: {name}')
    return name[0], name[1:]


class CampaignOcr:
    stage = {}
    chapter = 0

    def extract_campaign_name_image(self, image):
        result = TEMPLATE_STAGE_CLEAR.match_multi(image, similarity=0.95)
        # np.sort(result.flatten())[-10:]
        # array([0.8680386 , 0.8688129 , 0.8693155 , 0.86967576, 0.87012905,
        #        0.8705039 , 0.99954903, 0.99983317, 0.99996626, 1.        ],
        #       dtype=float32)

        name_offset = (70, 12)
        name_size = (60, 14)
        name_letter = (255, 255, 255)
        name_back = (102, 102, 102)
        digits = []
        for point in result:
            point = point[::-1]
            button = tuple(np.append(point, point + TEMPLATE_STAGE_CLEAR.image.shape[:2][::-1]))
            point = point + name_offset
            name = image.crop(np.append(point, point + name_size))
            name = extract_letters(name, letter=name_letter, back=name_back)
            stage = self.extract_stage_name(name)
            digits.append(Button(area=area_offset(stage, point), color=stage_clear_color, button=button, name='stage'))

        result = TEMPLATE_STAGE_PERCENT.match_multi(image, similarity=0.95)
        name_offset = (45, 3)
        for point in result:
            point = point[::-1]
            button = tuple(np.append(point, point + TEMPLATE_STAGE_PERCENT.image.shape[:2][::-1]))
            point = point + name_offset
            name = image.crop(np.append(point, point + name_size))
            name = extract_letters(name, letter=name_letter, back=name_back)
            stage = self.extract_stage_name(name)
            digits.append(
                Button(area=area_offset(stage, point), color=stage_percentage_color, button=button, name='stage'))

        if len(digits) == 0:
            logger.warning('No stage found.')

        return digits

    @staticmethod
    def extract_stage_name(image):
        x_skip = 10
        interval = 5
        x_color = np.convolve(np.mean(image, axis=0), np.ones(interval), 'valid') / interval
        x_list = np.where(x_color[x_skip:] > 235)[0]
        if x_list is None or len(x_list) == 0:
            logger.warning('No interval between digit and text.')

        return 0, 0, x_list[0] + 1 + x_skip, image.shape[0]

    @staticmethod
    def name_separate(image):
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

    def get_stage_name(self, image):
        self.stage = {}
        buttons = self.extract_campaign_name_image(image)

        ocr = Ocr(buttons, lang='stage', letter=(255, 255, 255), back=(102, 102, 102), threshold=180)
        result = ocr.ocr(image)
        if not isinstance(result, list):
            result = [result]
        result = [ocr_result_process(res) for res in result]

        chapter = [separate_name(res)[0] for res in result]
        counter = collections.Counter(chapter)
        self.chapter = counter.most_common()[0][0]

        for name, button in zip(result, buttons):
            button.area = button.button
            button.name = name
            self.stage[name] = button

        logger.attr('Chapter', self.chapter)
        logger.attr('Stage', ', '.join(self.stage.keys()))

    def get_chapter_index(self, image):
        """
        A tricky method for ui_ensure_index
        """
        try:
            self.get_stage_name(image)
        except IndexError:
            raise CampaignNameError

        return ensure_chapter_index(self.chapter)
