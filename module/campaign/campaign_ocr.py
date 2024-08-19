import collections

from module.base.base import ModuleBase
from module.base.decorator import Config, cached_property, del_cached_property
from module.base.timer import Timer
from module.base.utils import *
from module.exception import CampaignNameError
from module.logger import logger
from module.map.assets import WITHDRAW
from module.ocr.ocr import Ocr
from module.template.assets import *


class CampaignOcr(ModuleBase):
    stage_entrance = {}
    campaign_chapter = 0
    # An approximate area where stages will appear for faster template matching
    _stage_detect_area = (87, 117, 1151, 636)

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
            elif name in ['a', 'c', 'as', 'cs', 't', 'ht', 'ts', 'hts', 'sp', 'ex_sp']:
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
        name = name.strip('-')
        if name == 'sp':
            return 'ex_sp', '1'
        elif name.startswith('extra') or name == 'ex':
            return 'ex_ex', '1'
        elif '-' in name:
            return name.split('-')
        elif name.startswith('sp'):
            return 'sp', name[-1]
        elif name[-1].isdigit():
            return name[:-1], name[-1]
        elif name[0].isdigit() and name[-1].isalpha():
            # 49X
            logger.warning(f'Unknown stage name: {name}')
            return '', ''

        logger.warning(f'Unknown stage name: {name}')
        return '', ''

    def campaign_match_multi(self, template, image, stage_image=None, name_offset=(75, 9), name_size=(60, 16),
                             name_letter=(255, 255, 255), name_thresh=128, similarity=0.85):
        """
        Find stage entrances from the given image.

        Args:
            template (Template):
            image: Screenshot
            stage_image: Screenshot to find stage entrance.
            name_offset (tuple[int]):
            name_size (tuple[int]):
            name_letter (tuple[int]):
            name_thresh (int):
            similarity (float):

        Returns:
            list[Button]: Stage clear buttons.
        """
        digits = []
        stage_image = image if stage_image is None else stage_image
        result = template.match_multi(stage_image, similarity=similarity, name='STAGE')
        name_area = (name_offset[0], name_offset[1], name_offset[0] + name_size[0], name_offset[1] + name_size[1])
        for button in result:
            button = button.move(self._stage_detect_area[:2])
            button_name = button.crop(area=name_area, image=image)
            name = extract_letters(button_name.image, letter=name_letter, threshold=name_thresh)
            button_name = button_name.crop(area=self._extract_stage_name(name))
            # To each Button instance:
            # button.area: Area of stage name, such as '3-4'. Temporarily replaced for OCR.
            # button.color: Color of stage icon, such as 'CLEAR' and '%'.
            # button.button: Area of stage icon, such as 'CLEAR' and '%'.
            # button.name: 'STAGE', a meaningless name.
            button.load_color(image)
            button.area = button_name.area
            digits.append(button)

        return digits

    @cached_property
    def _stage_image(self):
        return crop(self.device.image, self._stage_detect_area, copy=False)

    @cached_property
    def _stage_image_gray(self):
        return rgb2gray(self._stage_image)

    @Config.when(SERVER='en')
    def campaign_extract_name_image(self, image):
        digits = []

        if 'normal' in self.config.STAGE_ENTRANCE:
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_CLEAR,
                image, self._stage_image_gray,
                name_offset=(70, 12), name_size=(60, 14)
            )
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_PERCENT,
                image, self._stage_image_gray,
                name_offset=(45, 3), name_size=(60, 14)
            )
        if 'half' in self.config.STAGE_ENTRANCE:
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_HALF_PERCENT,
                image, self._stage_image_gray,
                name_offset=(48, 0), name_size=(60, 16)
            )
        if 'blue' in self.config.STAGE_ENTRANCE:
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_BLUE_PERCENT,
                image, extract_letters(self._stage_image, letter=(255, 255, 255), threshold=153),
                name_offset=(55, 0), name_size=(60, 16)
            )
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_BLUE_CLEAR,
                image, extract_letters(self._stage_image, letter=(99, 223, 239), threshold=153),
                name_offset=(60, 12), name_size=(60, 16)
            )
        if 'green' in self.config.STAGE_ENTRANCE:
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_GREEN_CLEAR,
                image, self._stage_image_gray,
                name_offset=(60, 0), name_size=(60, 22)
            )
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_PERCENT,
                image, self._stage_image_gray,
                similarity=0.6,
                name_offset=(52, 0), name_size=(60, 22)
            )
        if '20240725' in self.config.STAGE_ENTRANCE:
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_CLEAR_20240725,
                image, self._stage_image_gray,
                name_offset=(73, -4), name_size=(60, 22)
            )

        return digits

    @Config.when(SERVER=None)
    def campaign_extract_name_image(self, image):
        """
        Find all stage entrance and handle event differences.
        Stage entrance setting, refers to ManualConfig.STAGE_ENTRANCE

        Args:
            image: Screenshot

        Returns:
            list[Button]: List of Buttons of stage entrance.
        """
        digits = []

        if 'normal' in self.config.STAGE_ENTRANCE:
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_CLEAR,
                image, self._stage_image_gray,
                name_offset=(75, 9), name_size=(60, 16)
            )
            # 2024.04.11 Game client bugged with random broken assets around TEMPLATE_STAGE_CLEAR
            # digits += self.campaign_match_multi(
            #     TEMPLATE_STAGE_CLEAR_SMALL,
            #     image, self._stage_image_gray,
            #     name_offset=(53, 2), name_size=(60, 16)
            # )
            # digits += self.campaign_match_multi(
            #     TEMPLATE_STAGE_HALF_PERCENT,
            #     image, self._stage_image_gray,
            #     name_offset=(48, 0), name_size=(60, 16)
            # )
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_PERCENT,
                image, self._stage_image_gray,
                name_offset=(48, 0), name_size=(60, 16)
            )
        if 'half' in self.config.STAGE_ENTRANCE:
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_HALF_PERCENT,
                image, self._stage_image_gray,
                name_offset=(48, 0), name_size=(60, 16)
            )
        if 'blue' in self.config.STAGE_ENTRANCE:
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_BLUE_PERCENT,
                image, extract_letters(self._stage_image, letter=(255, 255, 255), threshold=153),
                name_offset=(55, 0), name_size=(60, 16)
            )
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_BLUE_CLEAR,
                image, extract_letters(self._stage_image, letter=(99, 223, 239), threshold=153),
                name_offset=(60, 12), name_size=(60, 16)
            )
        if 'green' in self.config.STAGE_ENTRANCE:
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_GREEN_CLEAR,
                image, self._stage_image_gray,
                name_offset=(60, 0), name_size=(60, 22)
            )
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_PERCENT,
                image, self._stage_image_gray,
                similarity=0.6,
                name_offset=(52, 0), name_size=(60, 22)
            )
        if '20240725' in self.config.STAGE_ENTRANCE:
            digits += self.campaign_match_multi(
                TEMPLATE_STAGE_CLEAR_20240725,
                image, self._stage_image_gray,
                name_offset=(73, -4), name_size=(60, 22)
            )

        return digits

    @staticmethod
    def _extract_stage_name(image):
        """
        Args:
            image: Cropped image of full stage name, such as '3-4 Counterattack!'

        Returns:
            Area of stage name, such as the coordinate of '3-4' in the input image.
        """
        x_skip = 10
        interval = 5
        x_color = np.convolve(np.mean(image, axis=0), np.ones(interval), 'valid') / interval
        x_list = np.where(x_color[x_skip:] > 245)[0]
        if x_list is None or len(x_list) == 0:
            logger.warning('No interval between digit and text.')
            area = (0, 0, image.shape[1], image.shape[0])
        else:
            area = (0, 0, x_list[0] + 1 + x_skip, image.shape[0])
        return np.array(area) + (-3, -7, 3, 7)

    def _get_stage_name(self, image):
        """
        Parse stage names from a given image.
        Set attributes:
        self.campaign_chapter: str, Name of current chapter.
        self.stage_entrance: dict. Key, str, stage name. Value, Button, button to enter stage.

        Args:
            image (np.ndarray):
        """
        self.stage_entrance = {}
        del_cached_property(self, '_stage_image')
        del_cached_property(self, '_stage_image_gray')
        buttons = self.campaign_extract_name_image(image)
        del_cached_property(self, '_stage_image')
        del_cached_property(self, '_stage_image_gray')
        if len(buttons) == 0:
            logger.info('No stage found.')
            raise CampaignNameError

        ocr = Ocr(buttons, name='campaign', letter=(255, 255, 255), threshold=128,
                  alphabet='0123456789ABCDEFGHIJKLMNPQRSTUVWXYZ-')
        result = ocr.ocr(image)
        if not isinstance(result, list):
            result = [result]
        result = [self._campaign_ocr_result_process(res) for res in result]

        chapter = [self._campaign_separate_name(res)[0] for res in result if res]
        chapter = list(filter(('').__ne__, chapter))
        if not chapter:
            raise CampaignNameError

        counter = collections.Counter(chapter)
        self.campaign_chapter = counter.most_common()[0][0]

        if self.campaign_chapter == 0 or self.campaign_chapter == '0':
            # ['0F', 'F-IB', 'IGI']
            raise CampaignNameError

        # After OCR, recover button attributes.
        # These buttons are ready to be stage entrances for `MapOperation.enter_map()`
        # button.area: Area of stage name, such as 'CLEAR' and '%'.
        # button.color: Color of stage icon.
        # button.button: Area of stage icon.
        # button.name: Stage name, from OCR results.
        for name, button in zip(result, buttons):
            button.area = button.button
            button.name = name
            self.stage_entrance[name] = button

        logger.attr('Chapter', self.campaign_chapter)
        logger.attr('Stage', ', '.join(self.stage_entrance.keys()))

    def handle_get_chapter_additional(self):
        """
        Returns:
            bool: If clicked
        """
        if self.appear(WITHDRAW, offset=(30, 30)):
            logger.warning(f'get_chapter_index: WITHDRAW appears')
            raise CampaignNameError

    def get_chapter_index(self, skip_first_screenshot=True):
        """
        A tricky method for ui_ensure_index

        Args:
            skip_first_screenshot:

        Returns:
            int: Chapter index.
        """
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                raise CampaignNameError
            image = self.device.image
            try:
                self._get_stage_name(image)
                break
            except (IndexError, CampaignNameError):
                pass

            if self.handle_get_chapter_additional():
                continue

        return self._campaign_get_chapter_index(self.campaign_chapter)
