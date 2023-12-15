import re
from functools import partial

from module.base.decorator import Config
from module.base.filter import Filter
from module.base.timer import Timer
from module.config.config_generated import GeneratedConfig
from module.logger import logger
from module.research.assets import *
from module.research.preset import *
from module.research.project import research_detect, research_jp_detect
from module.research.ui import ResearchUI

RESEARCH_ENTRANCE = [ENTRANCE_1, ENTRANCE_2, ENTRANCE_3, ENTRANCE_4, ENTRANCE_5]
FILTER_REGEX = re.compile('(s[123456])?'
                          '-?'
                          '(neptune|monarch|ibuki|izumo|roon|saintlouis'
                          '|seattle|georgia|kitakaze|azuma|friedrich'
                          '|gascogne|champagne|cheshire|drake|mainz|odin'
                          '|anchorage|hakuryu|agir|august|marcopolo'
                          '|plymouth|rupprecht|harbin|chkalov|brest'
                          '|kearsarge|hindenburg|shimanto|schultz|flandre)?'
                          '(dr|pry)?'
                          '([bcdeghqt])?'
                          '-?'
                          '(\d{3})?'
                          '(\d.\d|\d\d?)?')
FILTER_ATTR = ('series', 'ship', 'ship_rarity', 'genre', 'number', 'duration')
FILTER_PRESET = ('shortest', 'cheapest', 'reset')
FILTER = Filter(FILTER_REGEX, FILTER_ATTR, FILTER_PRESET)


class ResearchSelector(ResearchUI):
    # List of current research projects
    projects: list
    # From StorageHandler
    storage_has_boxes = True

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

    def _research_jp_detect(self, skip_first_screenshot=True):
        """
        Wraps research_jp_detect() with error handling

        Args:
            skip_first_screenshot:

        Returns:
            ResearchProjectJp
        """
        timeout = Timer(2, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.info_bar_count():
                logger.info('Handle info_bar')
                timeout.reset()
                continue

            project = research_jp_detect(self.device.image)
            if project.duration == '0':
                logger.warning(f'Invalid research duration: {project}')
                continue
            else:
                return project

    @Config.when(SERVER='jp')
    def research_detect(self):
        """
        We do not need a screenshot here actually. 'image' is a null argument.
        Adding this argument is just to eusure all "research_detect" have the same arguments.
        """
        projects = []
        proj_sorted = []

        for _ in range(5):
            self.device.click_record_clear()
            """
            Every time entering the 4th(mid-right) entrance,
            all research subjects shift 1 position from right to left.
            """
            self.research_goto_detail(3)
            """
            'image' is a null argument as described above.
            What we need here is the current screen 'self.device.image'.
            """
            project = self._research_jp_detect()
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
        timeout = Timer(5, count=5).start()
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
                string = string + ' > ' + DICT_FILTER_PRESET[GeneratedConfig.Research_PresetFilter]
        else:
            if (self.config.Research_UseCube == 'always_use' or enforce) \
                    and f'{preset}_cube' in DICT_FILTER_PRESET:
                preset = f'{preset}_cube'
            if preset not in DICT_FILTER_PRESET:
                logger.warning(f'Preset not found: {preset}, use default preset')
                preset = GeneratedConfig.Research_PresetFilter
            string = DICT_FILTER_PRESET[preset]

        logger.attr('Research preset', preset)
        logger.info('Use cube: {} Use coin: {} Use part: {}'.format(
            self.config.Research_UseCube,
            self.config.Research_UseCoin,
            self.config.Research_UsePart))
        logger.attr('Allow delay', self.config.Research_AllowDelay)

        # Case insensitive
        string = string.lower()
        # Filter uses `hakuryu`, but allows both `hakuryu` and `hakuryuu`
        string = string.replace('hakuryuu', 'hakuryu')
        # Allow both `fastest` and `shortest`
        string = string.replace('fastest', 'shortest')
        # Allow both `PR` and `PRY`
        string = re.sub(r'pr([\d\- >])', r'pry\1', string)

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
        # 2022.08.23 Allow all E-2, disassemble equipment is now supported
        #   Ignore E-2 if don't have any boxes in storage to disassemble,
        #   Or will enter a loop of starting research, trying to disassemble, cancel research
        if not self.storage_has_boxes or self.config.SERVER in ['tw']:
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
