from datetime import timedelta

from scipy import signal

from module.base.decorator import cached_property
from module.base.utils import *
from module.logger import logger
from module.ocr.ocr import Duration, Ocr
from module.research.assets import *
from module.research.project_data import LIST_RESEARCH_PROJECT
from module.research.series import get_detail_series, get_research_series_3
from module.statistics.utils import *

RESEARCH_SERIES = (SERIES_1, SERIES_2, SERIES_3, SERIES_4, SERIES_5)
RESEARCH_STATUS = [STATUS_1, STATUS_2, STATUS_3, STATUS_4, STATUS_5]
OCR_RESEARCH = [OCR_RESEARCH_1, OCR_RESEARCH_2, OCR_RESEARCH_3, OCR_RESEARCH_4, OCR_RESEARCH_5]
OCR_RESEARCH = Ocr(OCR_RESEARCH, name='RESEARCH', threshold=64, alphabet='0123456789BCDEGHQTMIULRF-')
RESEARCH_DETAIL_GENRE = [DETAIL_GENRE_B, DETAIL_GENRE_C, DETAIL_GENRE_D, DETAIL_GENRE_E, DETAIL_GENRE_G,
                         DETAIL_GENRE_H_0, DETAIL_GENRE_H_1, DETAIL_GENRE_Q, DETAIL_GENRE_T]


def get_research_series_old(image, series_button=RESEARCH_SERIES):
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
        series_button:

    Returns:
        list[int]: Such as [1, 1, 1, 2, 3]
    """
    result = []
    # Set 'prominence = 50' to ignore possible noise.
    # 2021.07.18 Letter IV is now smaller than I, II, III, since the maintenance in 07.15.
    #   The "/" of the "V" in IV become darker because of anti-aliasing.
    #   So lower height to 160 to have a better detection.
    parameters = {'height': 160, 'prominence': 50, 'width': 1}

    for button in series_button:
        im = color_similarity_2d(resize(crop(image, button.area), (46, 25)), color=(255, 255, 255))
        peaks = [len(signal.find_peaks(row, **parameters)[0]) for row in im[5:-5]]
        upper, lower = max(peaks), min(peaks)
        # print(peaks)

        # Remove noise like [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2]
        if upper == 3 and lower == 2 and peaks.count(3) <= 2:
            upper = 2

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


def _get_research_series(img):
    # img = rgb2luma(img)
    img = extract_white_letters(img)
    pos = img.shape[0] * 2 // 5

    img = img[pos - 4:pos + 5]
    img = cv2.GaussianBlur(img, (5, 5), 1)
    img = img[3:6]

    threshold = np.mean(img)
    edge = np.where(np.diff((img[1] > threshold).astype(np.uint8)) == 1)[0]

    grad_x = cv2.Sobel(img, cv2.CV_16S, 1, 0)[1]
    grad_y = cv2.Sobel(img, cv2.CV_16S, 0, 1)[1]

    edge = np.arctan([
        grad_y[i] / grad_x[i]
        for i in edge
    ])
    edge = tuple(
        0 if i > -.1
        else 1
        for i in edge
        if i < .1
    )

    return {
        (0,): 1,
        (0, 0): 2,
        (0, 0, 0): 3,
        (0, 1): 4,
        (1,): 5,
        (1, 0): 6
    }.get(edge, 0)


def get_research_series(image, series_button=RESEARCH_SERIES):
    """
        Args:
        image (np.ndarray):
        series_button:

    Returns:
        list[int]: Such as [1, 1, 1, 2, 3]
    """
    result = []
    for button in series_button:
        # img = resize(crop(image, button.area), (46, 25))
        img = crop(image, button.area)
        img = cv2.resize(img, (46, 25), interpolation=cv2.INTER_AREA)
        series = _get_research_series(img)
        result.append(series)
    return result


def get_research_name(image, ocr=OCR_RESEARCH):
    """
    Args:
        image (np.ndarray):
        ocr (Ocr):

    Returns:
        list[str]: Such as ['D-057-UL', 'D-057-UL', 'D-057-UL', 'D-057-UL', 'D-057-UL']
    """
    names = ocr.ocr(image)
    if not isinstance(names, list):
        names = [names]
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


def get_research_series_jp_old(image):
    """
    Almost the same as get_research_series except the button area.

    Args:
        image (np.ndarray): Screenshot

    Returns:
        str: Series like "S4"
    """
    # Set 'prominence = 50' to ignore possible noise.
    parameters = {'height': 160, 'prominence': 50, 'width': 1}

    area = SERIES_DETAIL.area
    # Resize is not needed because only one area will be checked in JP server.
    im = color_similarity_2d(crop(image, area), color=(255, 255, 255))
    peaks = [len(signal.find_peaks(row, **parameters)[0]) for row in im[5:-5]]
    upper, lower = max(peaks), min(peaks)
    # print(upper, lower)

    # Remove noise like [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2]
    if upper == 3 and lower == 2 and peaks.count(3) <= 2:
        upper = 2

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


def get_research_series_jp(image):
    """
    Args:
        image:

    Returns:
        str: Series like "S4"
    """
    series = get_detail_series(image)
    return f'S{series}'


def get_research_duration_jp(image):
    """
    Args:
        image (np.ndarray): Screenshot

    Returns:
        duration (int): number of seconds
    """
    ocr = Duration(DURATION_DETAIL)
    duration = ocr.ocr(image).total_seconds()
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
        if button.match(image, offset=(30, 20), threshold=0.9):
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
    for name, series in zip(get_research_name(image), get_research_series_3(image)):
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
        '|plymouth|rupprecht|harbin|chkalov|brest'
        '|kearsarge|hindenburg|shimanto|schultz|flandre)')
    REGEX_INPUT = re.compile('(coin|cube|part)')
    REGEX_DR_SHIP = re.compile('azuma|friedrich|drake|hakuryu|agir|plymouth|brest|kearsarge|hindenburg')
    # Generate with:
    """
    out = []
    for row in LIST_RESEARCH_PROJECT:
        name = row['name']
        if name.startswith('D'):
            number = name.split('-')[1]
            out.append(number)
    print(out)
    """
    C_PROJECT_NUMBERS = ['153', '185', '038']
    D_PROJECT_NUMBERS = [
        '718', '731', '744', '759', '774', '792', '318', '331', '344', '359', '374', '392', '705', '712', '746', '757',
        '779', '794', '305', '312', '346', '357', '379', '394', '721', '722', '772', '777', '795', '321', '322', '372',
        '377', '395', '708', '763', '775', '782', '768', '308', '363', '375', '382', '368', '719', '778', '786', '788',
        '793', '319', '378', '386', '388', '393', '783', '713', '739', '771', '796', '383', '313', '339', '371', '396',
        '418', '431', '444', '459', '474', '492', '018', '031', '044', '059', '074', '092', '405', '412', '446', '457',
        '479', '494', '005', '012', '046', '057', '079', '094', '421', '422', '472', '477', '495', '021', '022', '072',
        '077', '095', '408', '463', '475', '482', '468', '008', '063', '075', '082', '068', '419', '478', '486', '488',
        '493', '019', '078', '086', '088', '093', '483', '413', '439', '471', '496', '083', '013', '039', '071', '096']

    def __init__(self, name, series):
        """
        Args:
            name (str): Such as 'D-057-UL'
            series (int): Such as 1, 2, 3
        """
        self.valid = True
        # '4'
        self.raw_series = series
        # 'S4'
        self.series = f'S{series}'
        # 'D-057-UL'
        self.name = self.check_name(name)
        if self.name != name:
            logger.info(f'Research name {name} is revised to {self.name}')
        # 'D'
        self.genre = ''
        # '057'
        self.number = ''
        # '0.5'
        self.duration = '24'
        # Ship face, like 'Azuma'
        self.ship = ''
        # 'dr' or 'pry'
        self.ship_rarity = ''
        self.need_coin = False
        self.need_cube = False
        self.need_part = False
        # Project requirements, like:
        # 'Scrap 8 pieces of gear.'
        self.task = ''

        matched = False
        for data in self.get_data(name=self.name, series=series):
            matched = True
            self.data = data
            self.genre = data['name'][0]
            self.number = data['name'][2:5]
            self.duration = str(data['time'] / 3600).rstrip('.0')
            self.task = data['task']
            for item in data['input']:
                item_name = item['name'].replace(' ', '').lower()
                result = re.search(ResearchProject.REGEX_INPUT, item_name)
                if result:
                    self.__setattr__(f'need_{result.group(1)}', True)
            for item in data['output']:
                item_name = item['name'].replace(' ', '').lower()
                result = re.search(ResearchProject.REGEX_SHIP, item_name)
                if not self.ship:
                    self.ship = result.group(1) if result else ''
                if self.ship:
                    self.ship_rarity = 'dr' if re.search(ResearchProject.REGEX_DR_SHIP, self.ship) else 'pry'
            break

        if not matched:
            logger.warning(f'Invalid research {self}')
            self.valid = False

    def __str__(self):
        if self.valid:
            return f'{self.series} {self.name}'
        else:
            return f'{self.series} {self.name} (Invalid)'

    def __eq__(self, other):
        return str(self) == str(other)

    def check_name(self, name):
        """
        Args:
            name (str):

        Returns:
            str:
        """
        name = name.strip('-')
        # G-185-MI, D-T85-MI -> C-185-MI
        name = name.replace('G-185', 'C-185').replace('D-T85', 'C-185')
        # E-316-MI -> E-315-MI
        if name == '316-MI':
            name = 'E-315-MI'

        parts = name.split('-')
        parts = [i for i in parts if i]
        if len(parts) == 3:
            prefix, number, suffix = parts

            number = number.replace('D', '0').replace('O', '0').replace('S', '5')
            # E-316-MI -> E-315-MI
            number = number.replace('316', '315')
            # [TW] S5 D-349-MI -> S5 D-319-MI
            if prefix == 'D' and number == '349' and self.raw_series == 5:
                number = '319'

            if prefix in ['I1', 'U']:
                prefix = 'D'
            prefix = prefix.strip('I1')
            # LC-038-RF -> C-038-RF
            prefix = prefix.replace('LC', 'C')

            # S3 D-022-MI (S3-Drake-0.5) detected as 'D-022-ML', because of Drake's white cloth.
            suffix = suffix.replace('ML', 'MI').replace('MIL', 'MI').replace('M1', 'MI')
            # S4 D-063-UL (S4-hakuryu-0.5) detected as 'D-063-0C'
            # D-057-DC -> D-057-UL
            suffix = suffix.replace('0C', 'UL').replace('UC', 'UL')
            suffix = suffix.replace('DC5', 'UL').replace('DC3', 'UL').replace('DC', 'UL')
            # D-075-UL1 -> D-075-UL
            suffix = suffix.replace('UL1', 'UL').replace('ULI', 'UL').replace('UL5', 'UL')

            if suffix == 'U':
                suffix = 'UL'
            # TW ocr errors, convert B to D
            if prefix == 'B' and number in ResearchProject.D_PROJECT_NUMBERS:
                prefix = 'D'
            # I-483-RF revised to -483-RF -> D-483-RF
            if prefix == '' and number in ResearchProject.D_PROJECT_NUMBERS:
                prefix = 'D'
            # L-153-MI -> C-153-MI
            if prefix == 'L' and number in ResearchProject.C_PROJECT_NUMBERS:
                prefix = 'C'
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
            for t in 'QGE':
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

    @cached_property
    def equipment_amount(self):
        # Scrap 8 pieces of gear.
        # Scrap 15 pieces of gear.
        if '8 piece' in self.task:
            return 8
        elif '15 piece' in self.task:
            return 15
        else:
            return 0


class ResearchProjectJp:
    GENRE = ['b', 'c', 'd', 'e', 'g', 'h', 'q', 't']
    DURATION = ['0.5', '1', '1.5', '2', '2.5', '3', '4', '5', '6', '8', '12']
    SHIP_S1 = ['neptune', 'monarch', 'ibuki', 'izumo', 'roon', 'saintlouis']
    SHIP_S2 = ['seattle', 'georgia', 'kitakaze', 'azuma', 'friedrich', 'gascogne']
    SHIP_S3 = ['champagne', 'cheshire', 'drake', 'mainz', 'odin']
    SHIP_S4 = ['anchorage', 'hakuryu', 'agir', 'august', 'marcopolo']
    SHIP_S5 = ['plymouth', 'rupprecht', 'harbin', 'chkalov', 'brest']
    SHIP_S6 = ['kearsarge', 'hindenburg', 'shimanto', 'schultz', 'flandre']
    SHIP_ALL = SHIP_S1 + SHIP_S2 + SHIP_S3 + SHIP_S4 + SHIP_S5 + SHIP_S6
    DR_SHIP = ['azuma', 'friedrich', 'drake', 'hakuryu', 'agir', 'plymouth', 'brest', 'kearsarge', 'hindenburg']

    def __init__(self):
        self.valid = True
        self.name = ''
        self.series = ''
        self.genre = ''
        self.number = ''
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

    def __eq__(self, other):
        return str(self) == str(other)

    @cached_property
    def equipment_amount(self):
        if self.genre == 'E' and self.duration == '2':
            # JP has no research names, can't distinguish E-031-MI and E-315-MI,
            # return the max value 15
            return 15
        else:
            return 0
