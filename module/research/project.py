import re

from scipy import signal

from module.base.utils import *
from module.logger import logger
from module.ocr.ocr import Ocr
from module.research.assets import *
from module.research.filter import Filter
from module.research.preset import *
from module.research.project_data import LIST_RESEARCH_PROJECT
from module.ui.ui import UI

RESEARCH_SERIES = [SERIES_1, SERIES_2, SERIES_3, SERIES_4, SERIES_5]
OCR_RESEARCH = [OCR_RESEARCH_1, OCR_RESEARCH_2, OCR_RESEARCH_3, OCR_RESEARCH_4, OCR_RESEARCH_5]
OCR_RESEARCH = Ocr(OCR_RESEARCH, name='RESEARCH', threshold=64, alphabet='0123456789BCDEGHQTMIULRF-')
FILTER_REGEX = re.compile('(s[123])?'
                          '-?'
                          '(neptune|monarch|ibuki|izumo|roon|saintlouis|seattle|georgia|kitakaze|azuma|friedrich|gascogne|champagne|cheshire|drake|mainz|odin)?'
                          '(dr|pry)?'
                          '([bcdeghqt])?'
                          '-?'
                          '(\d.\d|\d\d?)?')
FILTER_ATTR = ('series', 'ship', 'ship_rarity', 'genre', 'duration')
FILTER_PRESET = ('shortest', 'cheapest', 'reset')
FILTER = Filter(FILTER_REGEX, FILTER_ATTR, FILTER_PRESET)


def get_research_series(image):
    """
    Get research series using a simple color detection.
    May not be able to detect 'IV' and 'V' in the future research series.

    Args:
        image (PIL.Image.Image):

    Returns:
        list[int]: Such as [1, 1, 1, 2, 3]
    """
    result = []
    parameters = {'height': 200}

    for button in RESEARCH_SERIES:
        im = np.array(image.crop(button.area).resize((46, 25)).convert('L'))
        mid = np.mean(im[8:17, :], axis=0)
        peaks, _ = signal.find_peaks(mid, **parameters)
        series = len(peaks)
        if 1 <= series <= 3:
            result.append(series)
        else:
            result.append(0)
            logger.warning(f'Unknown research series: button={button}, series={series}')

    return result


def get_research_name(image):
    """
    Args:
        image (PIL.Image.Image):

    Returns:
        list[str]: Such as ['D-057-UL', 'D-057-UL', 'D-057-UL', 'D-057-UL', 'D-057-UL']
    """
    names = []
    for name in OCR_RESEARCH.ocr(image):
        # S3 D-022-MI (S3-Drake-0.5) detected as 'D-022-ML', because of Drake's white cloth.
        name = name.replace('ML', 'MI').replace('MIL', 'MI')
        names.append(name)
    return names


class ResearchProject:
    REGEX_SHIP = re.compile(
        '(neptune|monarch|ibuki|izumo|roon|saintlouis|seattle|georgia|kitakaze|azuma|friedrich|gascogne|champagne|cheshire|drake|mainz|odin)')
    REGEX_INPUT = re.compile('(coin|cube|part)')
    DR_SHIP = ['azuma', 'friedrich', 'drake']

    def __init__(self, name, series):
        """
        Args:
            name (str): Such as 'D-057-UL'
            series (int): Such as 1, 2, 3
        """
        self.valid = True
        # self.config = config
        self.name = self.check_name(name)
        self.series = f'S{series}'
        self.genre = ''
        self.duration = '24'
        self.ship = ''
        self.ship_rarity = ''
        self.need_coin = False
        self.need_cube = False
        self.need_part = False

        matched = False
        for data in self.get_data(name=self.name, series=series):
            matched = True
            self.data = data
            self.genre = data['name'][0]
            self.duration = str(data['time'] / 3600).rstrip('.0')
            for item in data['input']:
                result = re.search(self.REGEX_INPUT, item['name'].replace(' ', '').lower())
                if result:
                    self.__setattr__(f'need_{result.group(1)}', True)
            for item in data['output']:
                result = re.search(self.REGEX_SHIP, item['name'].replace(' ', '').lower())
                if not self.ship:
                    self.ship = result.group(1) if result else ''
                if self.ship:
                    self.ship_rarity = 'dr' if self.ship in self.DR_SHIP else 'pry'
            break

        if not matched:
            logger.warning(f'Invalid research {self}')
            self.valid = False

    def __str__(self):
        if self.valid:
            return f'{self.series} {self.name}'
        else:
            return f'{self.series} {self.name} (Invalid)'

    @staticmethod
    def check_name(name):
        """
        Args:
            name (str):

        Returns:
            str:
        """
        name = name.strip('-')
        parts = name.split('-')
        if len(parts) == 3:
            prefix, number, suffix = parts
            number = number.replace('D', '0').replace('O', '0').replace('S', '5')
            return '-'.join([prefix, number, suffix])
        return name

    def get_data(self, name, series):
        """
        Args:
            name (str): Such as 'D-057-UL'
            series (int): Such as 1, 2, 3

        Yields:
            dict:
        """
        for data in LIST_RESEARCH_PROJECT:
            if (data['series'] == series) and (data['name'] == name):
                yield data

        if name.startswith('D'):
            # Letter 'C' may recognized as 'D', because project card is shining.
            name1 = 'C' + self.name[1:]
            for data in LIST_RESEARCH_PROJECT:
                if (data['series'] == series) and (data['name'] == name1):
                    self.name = name1
                    yield data

        for data in LIST_RESEARCH_PROJECT:
            if (data['series'] == series) and (data['name'].rstrip('MIRFUL-') == name.rstrip('MIRFUL-')):
                yield data

        return False


class ResearchSelector(UI):
    projects: list

    def research_detect(self, image):
        """
        Args:
            image (PIL.Image.Image): Screenshots
        """
        projects = []
        for name, series in zip(get_research_name(image), get_research_series(image)):
            project = ResearchProject(name=name, series=series)
            logger.attr('Project', project)
            projects.append(project)

        self.projects = projects

    def research_sort_filter(self):
        """
        Returns:
            list: A list of str and int, such as [2, 3, 0, 'reset']
        """
        # Load filter string
        preset = self.config.RESEARCH_FILTER_PRESET
        if preset == 'customized':
            string = self.config.RESEARCH_FILTER_STRING
        else:
            if preset not in DICT_FILTER_PRESET:
                logger.warning(f'Preset not found: {preset}, use default preset')
                preset = 'series_3_than_2'
            string = DICT_FILTER_PRESET[preset]

        FILTER.load(string)
        priority = FILTER.apply(self.projects)
        priority = self._research_check_filter(priority)

        # Log
        logger.attr(
            'Filter_sort',
            ' > '.join([str(self.projects[index]) if isinstance(index, int) else index for index in priority]))
        return priority

    def _research_check_filter(self, priority):
        """
        Args:
            priority (list): A list of str and int, such as [2, 3, 0, 'reset']

        Returns:
            list: A list of str and int, such as [2, 3, 0, 'reset']
        """
        out = []
        for index in priority:
            if isinstance(index, str):
                out.append(index)
                continue
            proj = self.projects[index]
            if not proj.valid:
                continue
            if (not self.config.RESEARCH_USE_CUBE and proj.need_cube) \
                    or (not self.config.RESEARCH_USE_COIN and proj.need_coin) \
                    or (not self.config.RESEARCH_USE_PART and proj.need_part):
                continue
            # Reasons to ignore B series and E-2:
            # - Can't guarantee research condition satisfied.
            #   You may get nothing after a day of running, because you didn't complete the precondition.
            # - Low income from B series research.
            #   Gold B-4 basically equivalent to C-12, but needs a lot of oil.
            if (proj.genre.upper() == 'B') \
                    or (proj.genre.upper() == 'E' and str(proj.duration) != '6'):
                continue
            out.append(index)
        return out

    def research_sort_shortest(self):
        """
        Returns:
            list: A list of str and int, such as [2, 3, 0, 'reset']
        """
        FILTER.load(FILTER_STRING_SHORTEST)
        priority = FILTER.apply(self.projects)
        priority = self._research_check_filter(priority)

        logger.attr(
            'Shortest_sort',
            ' > '.join([str(self.projects[index]) if isinstance(index, int) else index for index in priority]))
        return priority

    def research_sort_cheapest(self):
        """
        Returns:
            list: A list of str and int, such as [2, 3, 0, 'reset']
        """
        FILTER.load(FILTER_STRING_CHEAPEST)
        priority = FILTER.apply(self.projects)
        priority = self._research_check_filter(priority)

        logger.attr(
            'Cheapest_sort',
            ' > '.join([str(self.projects[index]) if isinstance(index, int) else index for index in priority]))
        return priority
