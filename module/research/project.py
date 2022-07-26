import re
from datetime import timedelta
from functools import partial

from scipy import signal

from module.base.decorator import Config
from module.base.filter import Filter
from module.base.timer import Timer
from module.base.utils import *
from module.config.config_generated import GeneratedConfig
from module.logger import logger
from module.ocr.ocr import Ocr
from module.research.assets import *
from module.research.preset import *
from module.research.project_data import LIST_RESEARCH_PROJECT
from module.statistics.utils import *
from module.ui.ui import UI

RESEARCH_ENTRANCE = [ENTRANCE_1, ENTRANCE_2, ENTRANCE_3, ENTRANCE_4, ENTRANCE_5]
RESEARCH_SERIES = [SERIES_1, SERIES_2, SERIES_3, SERIES_4, SERIES_5]
RESEARCH_STATUS = [STATUS_1, STATUS_2, STATUS_3, STATUS_4, STATUS_5]
OCR_RESEARCH = [OCR_RESEARCH_1, OCR_RESEARCH_2, OCR_RESEARCH_3, OCR_RESEARCH_4, OCR_RESEARCH_5]
OCR_RESEARCH = Ocr(OCR_RESEARCH, name='RESEARCH', threshold=64, alphabet='0123456789BCDEGHQTMIULRF-')
RESEARCH_DETAIL_GENRE = [DETAIL_GENRE_B, DETAIL_GENRE_C, DETAIL_GENRE_D, DETAIL_GENRE_E, DETAIL_GENRE_G,
                         DETAIL_GENRE_H_0, DETAIL_GENRE_H_1, DETAIL_GENRE_Q, DETAIL_GENRE_T]
FILTER_REGEX = re.compile('(s[12345])?'
                          '-?'
                          '(neptune|monarch|ibuki|izumo|roon|saintlouis'
                          '|seattle|georgia|kitakaze|azuma|friedrich'
                          '|gascogne|champagne|cheshire|drake|mainz|odin'
                          '|anchorage|hakuryu|agir|august|marcopolo'
                          '|plymouth|rupprecht|harbin|chkalov|brest)?'
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
    Counting white lines to detect Roman numerals.

    -------               --- --   --
     | | |   --> 3 lines   |   \   /   --> 3 lines
     | | |                 |   \   /
     | | |   --> 3 lines   |    \ /    --> 2 lines
    -------               ---    v

    Args:
        image (np.ndarray):

    Returns:
        list[int]: Such as [1, 1, 1, 2, 3]
    """
    result = []
    # Set 'prominence = 50' to ignore possible noise.
    # 2021.07.18 Letter IV is now smaller than I, II, III, since the maintenance in 07.15.
    #   The "/" of the "V" in IV become darker because of anti-aliasing.
    #   So lower height to 160 to have a better detection.
    parameters = {'height': 160, 'prominence': 50, 'width': 1}

    for button in RESEARCH_SERIES:
        im = color_similarity_2d(resize(crop(image, button.area), (46, 25)), color=(255, 255, 255))
        peaks = [len(signal.find_peaks(row, **parameters)[0]) for row in im[5:-5]]
        upper, lower = max(peaks), min(peaks)
        # print(peaks)
        if upper == lower and 1 <= upper <= 3:
            series = upper
        elif upper == 3 and lower == 2:
            series = 4
        elif upper == 2 and lower == 1:
            series = 5
        else:
            series = 0
            logger.warning(f'Unknown research series: button={button}, upper={upper}, lower={lower}')
        result.append(series)

    return result


def get_research_name(image):
    """
    Args:
        image (np.ndarray):

    Returns:
        list[str]: Such as ['D-057-UL', 'D-057-UL', 'D-057-UL', 'D-057-UL', 'D-057-UL']
    """
    names = []
    for name in OCR_RESEARCH.ocr(image):
        names.append(name)
    return names


def get_research_finished(image):
    """
    Args:
        image (np.ndarray):

    Returns:
        int: Index of the finished project, 0 to 4. Return None if no project finished.
    """
    for index in [2, 1, 3, 0, 4]:
        button = RESEARCH_STATUS[index]
        color = get_color(image, button.area)
        if max(color) - min(color) < 40:
            logger.warning(f'Unexpected color: {color}')
            continue
        color_index = np.argmax(color)  # R, G, B
        if color_index == 1:
            return index  # Green
        elif color_index == 2:
            continue  # Blue
        else:
            logger.warning(f'Unexpected color: {color}')
            continue

    return None


def parse_time(string):
    """
    Args:
        string (str): Such as 01:00:00, 05:47:10, 17:50:51.
    Returns:
        timedelta: datetime.timedelta instance.
    """
    result = re.search('(\d+):(\d+):(\d+)', string)
    if not result:
        logger.warning(f'Invalid time string: {string}')
        return None
    else:
        result = [int(s) for s in result.groups()]
        return timedelta(hours=result[0], minutes=result[1], seconds=result[2])


def match_template(image, template, area, offset=30, threshold=0.85):
    """
    Args:
        image (np.ndarray): Screenshot
        template (np.ndarray):
        area (tuple): Crop area of image.
        offset (int, tuple): Detection area offset.
        threshold (float): 0-1. Similarity. Lower than this value will return float(0).
    Returns:
        similarity (float):
    """
    if isinstance(offset, tuple):
        offset = np.array((-offset[0], -offset[1], offset[0], offset[1]))
    else:
        offset = np.array((0, -offset, 0, offset))
    image = crop(image, offset + area)
    res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    _, sim, _, point = cv2.minMaxLoc(res)
    similarity = sim if sim >= threshold else 0.0
    return similarity


def get_research_series_jp(image):
    """
    Almost the same as get_research_series except the button area.

    Args:
        image (np.ndarray): Screenshot

    Returns:
        series (string):
    """
    # Set 'prominence = 50' to ignore possible noise.
    parameters = {'height': 160, 'prominence': 50, 'width': 1}

    area = SERIES_DETAIL.area
    # Resize is not needed because only one area will be checked in JP server.
    im = color_similarity_2d(crop(image, area), color=(255, 255, 255))
    peaks = [len(signal.find_peaks(row, **parameters)[0]) for row in im[5:-5]]
    upper, lower = max(peaks), min(peaks)
    # print(upper, lower)
    if upper == lower and 1 <= upper <= 3:
        series = upper
    elif upper == 3 and lower == 2:
        series = 4
    elif upper == 2 and lower == 1:
        series = 5
    else:
        series = 0
        logger.warning(f'Unknown research series: upper={upper}, lower={lower}')

    return f'S{series}'


def get_research_duration_jp(image):
    """
    Args:
        image (np.ndarray): Screenshot

    Returns:
        duration (int): number of seconds
    """
    ocr = Ocr(DURATION_DETAIL, alphabet='0123456789:')
    duration = parse_time(ocr.ocr(image)).total_seconds()
    return duration


def get_research_genre_jp(image):
    """
    Args:
        image (np.ndarray): Screenshot

    Returns:
        genre (string):
    """
    genre = ''
    for button in RESEARCH_DETAIL_GENRE:
        if button.match(image, offset=10, threshold=0.9):
            # DETAIL_GENRE_H_0.name.split("_")[2] == 'H'
            genre = button.name.split("_")[2]
            break
    if not genre:
        logger.warning(f'Not able to recognize research genre!')
    return genre


def get_research_cost_jp(image):
    """
    When the research has 1 cost item, the size of it is 78*78.
    When the research has 2 cost items, the size of each is 77*77.
    However, templates of coins, cubes, and plates differ a lot with each other,
    so simply setting a lower threshold while matching can do the job.

    Args:
        image (np.ndarray): Screenshot

    Returns:
        costs (string): dict
    """
    size_template = (78, 78)
    area_template = (0, 0, 78, 57)
    folder = './assets/stats_basic'
    templates = load_folder(folder)
    costs = {'coin': False, 'cube': False, 'plate': False}
    for name, template in templates.items():
        template = load_image(template)
        template = crop(resize(template, size_template), area_template)
        sim = match_template(image=image,
                             template=template,
                             area=DETAIL_COST.area,
                             offset=(10, 10),
                             threshold=0.8)
        if not sim:
            continue
        for cost in costs:
            if re.compile(cost).match(name.lower()):
                costs[cost] = True
                continue

    # Rename keys to be the same as attrs of ResearchProjectJp.
    costs['need_coin'] = costs.pop('coin')
    costs['need_cube'] = costs.pop('cube')
    costs['need_part'] = costs.pop('plate')
    return costs


def get_research_ship_jp(image):
    """
    Notice that 2.5, 5, and 8 hours' D research have 4 items, while 0.5 hours' one has 3,
    so the button DETAIL_BLUEPRINT should not cover only the first one of 4 items.

    Args:
        image (np.ndarray): Screenshot

    Returns:
        ship (string):
    """
    folder = './assets/research_blueprint'
    templates = load_folder(folder)
    similarity = 0.0
    ship = ''
    for name, template in templates.items():
        sim = match_template(image=image,
                             template=load_image(template),
                             area=DETAIL_BLUEPRINT.area,
                             offset=(10, 10),
                             threshold=0.9)
        if sim > similarity:
            similarity = sim
            ship = name
    if ship == '':
        logger.warning(f'Ship recognition failed')
    return ship


def research_jp_detect(image):
    """
    Args:
        image (np.ndarray): Screenshot

    Return:
        project (ResearchProjectJp):
    """
    project = ResearchProjectJp()
    project.series = get_research_series_jp(image)
    project.duration = str(get_research_duration_jp(image) / 3600).rstrip('.0')
    project.genre = get_research_genre_jp(image)
    costs = get_research_cost_jp(image)
    for cost in costs:
        project.__setattr__(cost, costs[cost])
    if project.genre.lower() == 'd':
        project.ship = get_research_ship_jp(image).lower()
    if project.ship:
        project.ship_rarity = 'dr' if project.ship in project.DR_SHIP else 'pry'
    project.name = f'{project.series}-{project.genre}-{project.duration}{project.ship}'
    if not project.check_valid():
        logger.warning(f'Invalid research {project}')
    return project


def research_detect(image):
    """
    Args:
        image (np.ndarray): Screenshot

    Return:
        list[ResearchProject]:
    """
    projects = []
    for name, series in zip(get_research_name(image), get_research_series(image)):
        project = ResearchProject(name=name, series=series)
        logger.attr('Project', project)
        projects.append(project)
    return projects


class ResearchProject:
    REGEX_SHIP = re.compile(
        '(neptune|monarch|ibuki|izumo|roon|saintlouis'
        '|seattle|georgia|kitakaze|azuma|friedrich'
        '|gascogne|champagne|cheshire|drake|mainz|odin'
        '|anchorage|hakuryu|agir|august|marcopolo'
        '|plymouth|rupprecht|harbin|chkalov|brest)')
    REGEX_INPUT = re.compile('(coin|cube|part)')
    DR_SHIP = ['azuma', 'friedrich', 'drake', 'hakuryu', 'agir', 'plymouth', 'brest']

    def __init__(self, name, series):
        """
        Args:
            name (str): Such as 'D-057-UL'
            series (int): Such as 1, 2, 3
        """
        self.valid = True
        # self.config = config
        self.name = self.check_name(name)
        if self.name != name:
            logger.info(f'Research name {name} is revised to {self.name}')
        self.series = f'S{series}'
        self.genre = ''
        self.duration = '24'
        self.ship = ''
        self.ship_rarity = ''
        self.need_coin = False
        self.need_cube = False
        self.need_part = False
        self.task = ''

        matched = False
        for data in self.get_data(name=self.name, series=series):
            matched = True
            self.data = data
            self.genre = data['name'][0]
            self.duration = str(data['time'] / 3600).rstrip('.0')
            self.task = data['task']
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

    def check_name(self, name):
        """
        Args:
            name (str):

        Returns:
            str:
        """
        name = name.strip('-')
        parts = name.split('-')
        parts = [i for i in parts if i]
        if len(parts) == 3:
            prefix, number, suffix = parts
            number = number.replace('D', '0').replace('O', '0').replace('S', '5')
            if prefix == 'I1':
                prefix = 'D'
            prefix = prefix.strip('I1')
            # S3 D-022-MI (S3-Drake-0.5) detected as 'D-022-ML', because of Drake's white cloth.
            suffix = suffix.replace('ML', 'MI').replace('MIL', 'MI')
            # S4 D-063-UL (S4-hakuryu-0.5) detected as 'D-063-0C'
            suffix = suffix.replace('0C', 'UL').replace('UC', 'UL')
            return '-'.join([prefix, number, suffix])
        elif len(parts) == 2:
            # Trying to insert '-', for results like H339-MI
            if name[0].isalpha() and name[1].isdigit():
                return self.check_name(f'{name[0]}-{name[1:]}')
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

        if len(name) and name[0].isdigit():
            for t in 'QG':
                name1 = f'{t}-{self.name}'
                logger.info(f'Testing the most similar candidate {name1}')
                for data in LIST_RESEARCH_PROJECT:
                    if (data['series'] == series) and (data['name'] == name1):
                        self.name = name1
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


class ResearchProjectJp:
    GENRE = ['b', 'c', 'd', 'e', 'g', 'h', 'q', 't']
    DURATION = ['0.5', '1', '1.5', '2', '2.5', '3', '4', '5', '6', '8', '12']
    SHIP_S1 = ['neptune', 'monarch', 'ibuki', 'izumo', 'roon', 'saintlouis']
    SHIP_S2 = ['seattle', 'georgia', 'kitakaze', 'azuma', 'friedrich', 'gascogne']
    SHIP_S3 = ['champagne', 'cheshire', 'drake', 'mainz', 'odin']
    SHIP_S4 = ['anchorage', 'hakuryu', 'agir', 'august', 'marcopolo']
    SHIP_S5 = ['plymouth', 'rupprecht', 'harbin', 'chkalov', 'brest']
    SHIP_ALL = SHIP_S1 + SHIP_S2 + SHIP_S3 + SHIP_S4 + SHIP_S5
    DR_SHIP = ['azuma', 'friedrich', 'drake', 'hakuryu', 'agir', 'plymouth', 'brest']

    def __init__(self):
        self.valid = True
        self.name = ''
        self.series = ''
        self.genre = ''
        self.duration = '24'
        self.ship = ''
        self.ship_rarity = ''
        self.need_coin = False
        self.need_cube = False
        self.need_part = False
        self.task = ''

    def check_valid(self):
        self.valid = False
        if self.series.lower() == "s0":
            return False
        if self.genre.lower() not in self.GENRE:
            return False
        if self.duration not in self.DURATION:
            return False
        if self.ship not in self.SHIP_ALL:
            self.ship = ''
        if self.genre.lower() == 'd' and not self.ship:
            return False
        self.valid = True
        return True

    def __str__(self):
        if self.valid:
            return f'{self.name}'
        else:
            return f'{self.name} (Invalid)'


class ResearchSelector(UI):
    projects: list

    def research_goto_detail(self, index, skip_first_screenshot=True):
        logger.info(f'Research goto detail (project {index})')
        click_timer = Timer(10)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # DETAIL_NEXT appears even when the research detail page is not fully loaded.
            if not self.appear(DETAIL_NEXT, offset=(20, 20)):
                if click_timer.reached():
                    self.device.click(RESEARCH_ENTRANCE[index])
                    click_timer.reset()
            else:
                # Check RESEARCH_COST_CHECKER to ensure that the research detail page is fully loaded.
                self.wait_until_appear(RESEARCH_COST_CHECKER, offset=(20, 20), skip_first_screenshot=True)
                break

    def research_detail_quit(self, skip_first_screenshot=True):
        logger.info('Research detail quit')
        click_timer = Timer(10)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(RESEARCH_UNAVAILABLE, offset=(20, 20)) \
                    or self.appear(RESEARCH_START, offset=(20, 20)) \
                    or self.appear(RESEARCH_STOP, offset=(20, 20)):
                if click_timer.reached():
                    self.device.click(RESEARCH_DETAIL_QUIT)
                    click_timer.reset()
            else:
                self.wait_until_stable(STABLE_CHECKER_CENTER)
                break

    @Config.when(SERVER='jp')
    def research_detect(self):
        """
        We do not need a screenshot here actually. 'image' is a null argument.
        Adding this argument is just to eusure all "research_detect" have the same arguments.
        """
        projects = []
        proj_sorted = []

        for _ in range(5):
            """
            Every time entering the 4th(mid-right) entrance,
            all research subjects shift 1 position from right to left.
            """
            self.research_goto_detail(3)
            """
            'image' is a null argument as described above.
            What we need here is the current screen 'self.device.image'.
            """
            project = research_jp_detect(self.device.image)
            logger.attr('Project', project)
            projects.append(project)
            self.research_detail_quit()
        """
        page_research should remain the same as before.
        Since we entered the 4th entrance first,
        the indexes from left to right are (2, 3, 4, 0, 1).
        """
        for pos in range(5):
            proj_sorted.append(projects[(pos + 2) % 5])

        self.projects = proj_sorted

    @Config.when(SERVER=None)
    def research_detect(self):
        timeout = Timer(3, count=3).start()
        while 1:
            projects = research_detect(self.device.image)

            if timeout.reached():
                logger.warning('Failed to OCR research name after 3 trial, assume correct')
                break

            if sum([p.valid for p in projects]) < 5:
                # Leftmost research series covered by battle pass info, see #1037
                logger.info('Invalid project detected')
                logger.info('Probably because of battle pass info or too fast screenshot')
                # A rare case, poor sleep is acceptable
                self.device.sleep(1)
                self.device.screenshot()
                continue
            else:
                break

        self.projects = projects

    def research_sort_filter(self, enforce=False):
        """
        Returns:
            list: A list of ResearchProject objects and preset strings,
                such as [object, object, object, 'reset']
        """
        # Load filter string
        preset = self.config.Research_PresetFilter
        if preset == 'custom':
            string = self.config.Research_CustomFilter
            if enforce:
                value = GeneratedConfig.Research_PresetFilter
                string = string.split()
                string.append('>')
                string.extend(DICT_FILTER_PRESET[value].split())
                string = " ".join(string)
        else:
            if self.config.Research_UseCube == 'always_use' or enforce:
                if f'{preset}_cube' in DICT_FILTER_PRESET:
                    preset = f'{preset}_cube'
            if preset not in DICT_FILTER_PRESET:
                logger.warning(f'Preset not found: {preset}, use default preset')
                preset = 'series_5_blueprint_152'
            string = DICT_FILTER_PRESET[preset]

        logger.attr('Research preset', preset)
        logger.info('Use cube: {} Use coin: {} Use part: {}'.format(
            self.config.Research_UseCube,
            self.config.Research_UseCoin,
            self.config.Research_UsePart))
        logger.attr('Allow delay', self.config.Research_AllowDelay)

        # Filter uses `hakuryu`, but allows both `hakuryu` and `hakuryuu`
        string = string.lower().replace('hakuryuu', 'hakuryu')

        FILTER.load(string)
        priority = FILTER.apply(self.projects, func=partial(self._research_check, enforce=enforce))

        # Log
        logger.attr('Filter_sort', ' > '.join([str(project) for project in priority]))
        return priority

    def _research_check(self, project, enforce=False):
        """
        Args:
            project (ResearchProject):
            enforce (Bool):
        Returns:
            bool:
        """
        if not project.valid:
            return False

        # Check project consumption
        is_05 = str(project.duration) == '0.5'
        if project.need_cube:
            if self.config.Research_UseCube == 'do_not_use':
                return False
            if self.config.Research_UseCube == 'only_no_project' and not enforce:
                return False
            if self.config.Research_UseCube == 'only_05_hour' and not is_05 and not enforce:
                return False
        if project.need_coin:
            if self.config.Research_UseCoin == 'do_not_use':
                return False
            if self.config.Research_UseCoin == 'only_no_project' and not enforce:
                return False
            if self.config.Research_UseCoin == 'only_05_hour' and not is_05 and not enforce:
                return False
        if project.need_part:
            if self.config.Research_UsePart == 'do_not_use':
                return False
            if self.config.Research_UsePart == 'only_no_project' and not enforce:
                return False
            if self.config.Research_UsePart == 'only_05_hour' and not is_05 and not enforce:
                return False

        # Reasons to ignore B series and E-2:
        # - Can't guarantee research condition satisfied.
        #   You may get nothing after a day of running, because you didn't complete the precondition.
        # - Low income from B series research.
        #   Gold B-4 basically equivalent to C-12, but needs a lot of oil.

        if project.genre.upper() == 'B':
            return False
        # T series require commission
        # 2022.05.08 Allow T series researches because commission is now force to enable
        # 2022.07.17 Disallow T again cause they can't be queued unless pre-conditions satisfied
        if project.genre.upper() == 'T':
            return False
        # 2021.08.19 Allow E-2 to disassemble tech boxes, but JP still remains the same.
        if self.config.SERVER == 'jp':
            if project.genre.upper() == 'E' and str(project.duration) != '6':
                return False
        else:
            if project.genre.upper() == 'E' and project.task != '':
                return False

        return True

    def research_sort_shortest(self, enforce):
        """
        Returns:
            list: A list of ResearchProject objects and preset strings,
                such as [object, object, object, 'reset']
        """
        FILTER.load(FILTER_STRING_SHORTEST)
        priority = FILTER.apply(self.projects, func=partial(self._research_check, enforce=enforce))

        logger.attr('Filter_sort', ' > '.join([str(project) for project in priority]))
        return priority

    def research_sort_cheapest(self, enforce):
        """
        Returns:
            list: A list of ResearchProject objects and preset strings,
                such as [object, object, object, 'reset']
        """
        FILTER.load(FILTER_STRING_CHEAPEST)
        priority = FILTER.apply(self.projects, func=partial(self._research_check, enforce=enforce))

        logger.attr('Filter_sort', ' > '.join([str(project) for project in priority]))
        return priority
