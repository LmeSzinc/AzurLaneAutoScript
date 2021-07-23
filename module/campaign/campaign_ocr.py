import collections

from module.base.base import ModuleBase
from module.base.decorator import Config
from module.base.utils import *
from module.exception import CampaignNameError
from module.logger import logger
from module.map_detection.utils import Points
from module.ocr.ocr import Ocr
from module.template.assets import *


class CampaignOcr(ModuleBase):
    stage_entrance = {}
    campaign_chapter = 0

    @staticmethod
    def _campaign_get_chapter_index(name):
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
            elif name in ['a', 'c', 'as', 'cs', 'sp', 'ex_sp']:
                return 1
            elif name in ['b', 'd', 'bs', 'ds', 'ex_ex']:
                return 2
            else:
                raise CampaignNameError

    @staticmethod
    def _campaign_ocr_result_process(result):
        # The result will be like '7--2', because tha dash in game is '–' not '-'
        result = result.lower().replace('--', '-').replace('--', '-')
        if result.startswith('-'):
            result = result[1:]
        if len(result) == 2 and result[0].isdigit():
            result = '-'.join(result)
        return result

    @staticmethod
    def _campaign_separate_name(name):
        """
        Args:
            name (str): Stage name in lowercase, such as 7-2, d3, sp3.

        Returns:
            tuple[str]: Campaign_name and stage index in lowercase, Such as ['7', '2'], ['d', '3'], ['sp', '3'].
        """
        if name == 'sp':
            return 'ex_sp', '1'
        elif name.startswith('extra'):
            return 'ex_ex', '1'
        elif '-' in name:
            return name.split('-')
        elif name.startswith('sp'):
            return 'sp', name[-1]
        elif name[-1].isdigit():
            return name[:-1], name[-1]

        logger.warning(f'Unknown stage name: {name}')
        return name[0], name[1:]

    def campaign_match_multi(self, template, image, stage_image=None, name_offset=(75, 9), name_size=(60, 16),
                             name_letter=(255, 255, 255), name_thresh=128, similarity=0.85):
        """
        Args:
            template (Template):
            image: Screenshot
            stage_image: Screenshot to find stage entrance.
            name_offset (tuple[int]):
            name_size (tuple[int]):
            name_letter (tuple[int]):
            name_thresh (int):

        Returns:
            list[Button]: Stage clear buttons.
        """
        digits = []
        stage_image = image if stage_image is None else stage_image
        result = template.match_multi(stage_image, similarity=similarity)
        result = Points(result, config=self.config).group()

        for point in result:
            button = tuple(np.append(point, point + template.size))
            point = point + name_offset
            name = image.crop(np.append(point, point + name_size))
            name = extract_letters(name, letter=name_letter, threshold=name_thresh)
            stage = self._extract_stage_name(name)

            area = area_offset(stage, point)
            color = get_color(image, button)
            digits.append(Button(area=area, color=color, button=button, name='stage'))

        return digits

    @Config.when(SERVER='en')
    def campaign_extract_name_image(self, image):
        digits = []

        if 'normal' in self.config.STAGE_ENTRANCE:
            digits += self.campaign_match_multi(TEMPLATE_STAGE_CLEAR, image, name_offset=(70, 12), name_size=(60, 14))
            digits += self.campaign_match_multi(TEMPLATE_STAGE_PERCENT, image, name_offset=(45, 3), name_size=(60, 14))
        if 'half' in self.config.STAGE_ENTRANCE:
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_HALF_PERCENT, image, name_offset=(48, 0), name_size=(60, 16))
        if 'blue' in self.config.STAGE_ENTRANCE:
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_BLUE_PERCENT, image, extract_letters(image, letter=(255, 255, 255), threshold=153),
                name_offset=(55, 0), name_size=(60, 16))
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_BLUE_CLEAR, image, extract_letters(image, letter=(99, 223, 239), threshold=153),
                name_offset=(60, 12), name_size=(60, 16))

        return digits

    @Config.when(SERVER=None)
    def campaign_extract_name_image(self, image):
        digits = []

        if 'normal' in self.config.STAGE_ENTRANCE:
            digits += self.campaign_match_multi(TEMPLATE_STAGE_CLEAR, image, name_offset=(75, 9), name_size=(60, 16))
            digits += self.campaign_match_multi(TEMPLATE_STAGE_PERCENT, image, name_offset=(48, 0), name_size=(60, 16))
        if 'half' in self.config.STAGE_ENTRANCE:
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_HALF_PERCENT, image, name_offset=(48, 0), name_size=(60, 16))
        if 'blue' in self.config.STAGE_ENTRANCE:
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_BLUE_PERCENT, image, extract_letters(image, letter=(255, 255, 255), threshold=153),
                name_offset=(55, 0), name_size=(60, 16))
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_BLUE_CLEAR, image, extract_letters(image, letter=(99, 223, 239), threshold=153),
                name_offset=(60, 12), name_size=(60, 16))

        return digits

    @staticmethod
    def _extract_stage_name(image):
        x_skip = 10
        interval = 5
        x_color = np.convolve(np.mean(image, axis=0), np.ones(interval), 'valid') / interval
        x_list = np.where(x_color[x_skip:] > 235)[0]
        if x_list is None or len(x_list) == 0:
            logger.warning('No interval between digit and text.')
            area = (0, 0, image.shape[1], image.shape[0])
        else:
            area = (0, 0, x_list[0] + 1 + x_skip, image.shape[0])
        return np.array(area) + (-3, -7, 3, 7)

    def _get_stage_name(self, image):
        self.stage_entrance = {}
        buttons = self.campaign_extract_name_image(image)
        if len(buttons) == 0:
            logger.warning('No stage found.')

        ocr = Ocr(buttons, name='campaign', letter=(255, 255, 255), threshold=128,
                  alphabet='0123456789ABCDEFGHIJKLMNPQRSTUVWXYZ-')
        result = ocr.ocr(image)
        if not isinstance(result, list):
            result = [result]
        result = [self._campaign_ocr_result_process(res) for res in result]

        chapter = [self._campaign_separate_name(res)[0] for res in result]
        chapter = list(filter(('').__ne__, chapter))
        if not chapter:
            raise CampaignNameError

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

        return self._campaign_get_chapter_index(self.campaign_chapter)
