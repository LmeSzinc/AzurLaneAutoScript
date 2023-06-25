import re
from functools import cached_property
from typing import Iterator

from module.base.base import ModuleBase
from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import DigitCounter, Ocr
from module.ui.draggable_list import DraggableList
from module.ui.switch import Switch
from tasks.assignment.assets.assets_assignment_ui import *
from tasks.assignment.keywords import *
from tasks.base.page import page_assignment
from tasks.base.ui import UI


class AssignmentSwitch(Switch):
    def __init__(self, name, active_color: tuple[int, int, int], is_selector=True):
        super().__init__(name, is_selector)
        self.active_color = active_color

    def get(self, main: ModuleBase):
        """
        Use image_color_count instead to determine whether the button is selected/active

        Args:
            main (ModuleBase):

        Returns:
            str: state name or 'unknown'.
        """
        for data in self.state_list:
            if main.image_color_count(data['check_button'], self.active_color):
                return data['state']

        return 'unknown'


class AssignmentOcr(Ocr):
    OCR_REPLACE = {
        'ch': [
            (KEYWORDS_ASSIGNMENT_ENTRY.Winter_Soldiers.name, '[黑]冬的战士们'),
            (KEYWORDS_ASSIGNMENT_ENTRY.Born_to_Obey.name, '[牛]而服从'),
            (KEYWORDS_ASSIGNMENT_ENTRY.Root_Out_the_Turpitude.name,
             '根除恶[擎薯尊掌鞋]?'),
            (KEYWORDS_ASSIGNMENT_ENTRY.Akashic_Records.name, '阿[未][夏复]记录'),
        ]
    }

    @cached_property
    def ocr_regex(self) -> re.Pattern | None:
        rules = AssignmentOcr.OCR_REPLACE.get(self.lang)
        if rules is None:
            return None
        return re.compile('|'.join('(?P<%s>%s)' % pair for pair in rules))

    def after_process(self, result: str):
        result = super().after_process(result)
        if self.ocr_regex is None:
            return result
        matched = self.ocr_regex.fullmatch(result)
        if matched is None:
            return result
        keyword_lang = self.lang
        if self.lang == 'ch':
            keyword_lang = 'cn'
        matched = getattr(KEYWORDS_ASSIGNMENT_ENTRY, matched.lastgroup)
        matched = getattr(matched, keyword_lang)
        logger.attr(name=f'{self.name} after_process',
                    text=f'{result} -> {matched}')
        return matched


ASSIGNMENT_TOP_SWITCH = AssignmentSwitch(
    'AssignmentTopSwitch',
    (240, 240, 240)
)
ASSIGNMENT_TOP_SWITCH.add_state(
    KEYWORDS_ASSIGNMENT_GROUP.Character_Materials,
    check_button=CHARACTER_MATERIALS
)
ASSIGNMENT_TOP_SWITCH.add_state(
    KEYWORDS_ASSIGNMENT_GROUP.EXP_Materials_Credits,
    check_button=EXP_MATERIALS_CREDITS
)
ASSIGNMENT_TOP_SWITCH.add_state(
    KEYWORDS_ASSIGNMENT_GROUP.Synthesis_Materials,
    check_button=SYNTHESIS_MATERIALS
)

ASSIGNMENT_ENTRY_LIST = DraggableList(
    'AssignmentEntryList',
    keyword_class=AssignmentEntry,
    ocr_class=AssignmentOcr,
    search_button=OCR_ASSIGNMENT_LIST,
    check_row_order=False,
    active_color=(40, 40, 40)
)


class AssignmentUI(UI):
    def goto_group(self, group: AssignmentGroup):
        """
        Args:
            group (AssignmentGroup):

        Examples:
            self = AssignmentUI('src')
            self.device.screenshot()
            self.goto_group(KEYWORDS_ASSIGNMENT_GROUP.Character_Materials)
        """
        logger.hr('Assignment group goto', level=3)
        if ASSIGNMENT_TOP_SWITCH.set(group, main=self):
            self._wait_until_entry_loaded()

    def goto_entry(self, entry: AssignmentEntry):
        """
        Args:
            entry (AssignmentEntry):

        Examples:
            self = AssignmentUI('src')
            self.device.screenshot()
            self.goto_entry(KEYWORDS_ASSIGNMENT_ENTRY.Nameless_Land_Nameless_People)
        """
        self.goto_group(entry.group)
        ASSIGNMENT_ENTRY_LIST.select_row(entry, self)

    def _wait_until_entry_loaded(self):
        skip_first_screenshot = True
        timeout = Timer(2, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait entry loaded timeout')
                break
            # Maybe not reliable
            if self.image_color_count(ENTRY_LOADED, (35, 35, 35)):
                logger.info('Entry loaded')
                break

    @property
    def _limit_status(self) -> tuple[int, int, int]:
        self.device.screenshot()
        return DigitCounter(OCR_ASSIGNMENT_LIMIT).ocr_single_line(self.device.image)

    def _iter_groups(self) -> Iterator[AssignmentGroup]:
        for state in ASSIGNMENT_TOP_SWITCH.state_list:
            yield state['state']

    def _iter_entries(self) -> Iterator[AssignmentEntry]:
        """
        Iterate entries from top to bottom
        """
        ASSIGNMENT_ENTRY_LIST.load_rows(main=self)
        for button in ASSIGNMENT_ENTRY_LIST.cur_buttons:
            yield button.matched_keyword
