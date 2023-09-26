from datetime import datetime, timedelta

from module.base.base import ModuleBase
from module.base.timer import Timer
from module.config.stored.classes import now
from module.logger import logger
from module.ui.switch import Switch
from tasks.assignment.assets.assets_assignment_dispatch import *
from tasks.assignment.assets.assets_assignment_ui import DISPATCHED
from tasks.assignment.keywords import *
from tasks.assignment.ui import AssignmentUI


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


ASSIGNMENT_DURATION_SWITCH = AssignmentSwitch(
    'AssignmentDurationSwitch',
    (160, 130, 100)
)
ASSIGNMENT_DURATION_SWITCH.add_state('4', DURATION_4)
ASSIGNMENT_DURATION_SWITCH.add_state('8', DURATION_8)
ASSIGNMENT_DURATION_SWITCH.add_state('12', DURATION_12)
ASSIGNMENT_DURATION_SWITCH.add_state('20', DURATION_20)


class AssignmentDispatch(AssignmentUI):
    dispatched: dict[AssignmentEntry, datetime] = dict()
    has_new_dispatch: bool = False

    def dispatch(self, assignment: AssignmentEntry, duration: int | None):
        """
        Dispatch assignment.
        Should be called only when limit is checked

        Args:
            assignment (AssignmentEntry):
            duration (int | None): user specified duration, None for event assignments

        Pages:
            in: EMPTY_SLOT
            out: DISPATCHED
        """
        self._select_characters()
        if isinstance(assignment, AssignmentEventEntry):
            self._select_support()
            duration = self._get_assignment_time().total_seconds() / 3600
        else:
            self._select_duration(duration)
        self._confirm_assignment()
        self._wait_until_assignment_started()
        future = now() + timedelta(hours=duration)
        logger.info(f'Assignment dispatched, will finish at {future}')
        self.dispatched[assignment] = future
        self.has_new_dispatch = True

    def _select_characters(self):
        """
        Pages:
            in: EMPTY_SLOT
            out: CHARACTER_LIST
        """
        skip_first_screenshot = True
        self.interval_clear(
            (CHARACTER_LIST, CHARACTER_1_SELECTED, CHARACTER_2_SELECTED), interval=2)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            if self.match_template_color(CONFIRM_ASSIGNMENT):
                logger.info('Characters are all selected')
                break
            # Ensure character list
            # Search EMPTY_SLOT to load offset
            if not self.appear(CHARACTER_LIST) and self.appear(EMPTY_SLOT):
                if self.interval_is_reached(CHARACTER_LIST, interval=2):
                    self.interval_reset(CHARACTER_LIST, interval=2)
                    self.device.click(EMPTY_SLOT)
                continue
            # Select
            if self.interval_is_reached(CHARACTER_1_SELECTED, interval=2):
                self.interval_reset(CHARACTER_1_SELECTED, interval=2)
                if not self.image_color_count(CHARACTER_1_SELECTED, (240, 240, 240)):
                    self.device.click(CHARACTER_1)
            if self.interval_is_reached(CHARACTER_2_SELECTED, interval=2):
                self.interval_reset(CHARACTER_2_SELECTED, interval=2)
                if not self.image_color_count(CHARACTER_2_SELECTED, (240, 240, 240)):
                    self.device.click(CHARACTER_2)

    def _select_support(self):
        skip_first_screenshot = True
        self.interval_clear(
            (CHARACTER_SUPPORT_LIST, CHARACTER_SUPPORT_SELECTED), interval=2)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            if self.match_color(CHARACTER_SUPPORT_SELECTED):
                logger.info('Support character is selected')
                break
            # Ensure support list
            if not self.appear(CHARACTER_SUPPORT_LIST):
                if self.interval_is_reached(CHARACTER_SUPPORT_LIST, interval=2):
                    self.interval_reset(CHARACTER_SUPPORT_LIST, interval=2)
                    self.device.click(EMPTY_SLOT_SUPPORT)
                continue
            # Select
            if self.interval_is_reached(CHARACTER_SUPPORT_SELECTED, interval=2):
                self.interval_reset(CHARACTER_SUPPORT_SELECTED, interval=2)
                self.device.click(CHARACTER_SUPPORT)

    def _select_duration(self, duration: int):
        if duration not in {4, 8, 12, 20}:
            logger.warning(
                f'Duration {duration} is out of scope, reset it to 20')
            duration = 20
        ASSIGNMENT_DURATION_SWITCH.set(str(duration), self)

    def _confirm_assignment(self):
        """
        Pages:
            in: CONFIRM_ASSIGNMENT
            out: DISPATCHED
        """
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            if self.appear(DISPATCHED):
                logger.info(f'Assignment dispatched')
                break
            # Click
            if self.appear_then_click(CONFIRM_ASSIGNMENT, interval=2):
                continue

    def _wait_until_assignment_started(self):
        """
        Pages:
            in: DISPATCHED
            out: ASSIGNMENT_STARTED_CHECK
        """
        skip_first_screenshot = True
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            if self.appear(ASSIGNMENT_START):
                logger.info('Assignment start')
                break
            # Timeout
            if timeout.reached():
                logger.warning('Wait for assignment start timeout')
                break
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            if self.appear(ASSIGNMENT_STARTED_CHECK):
                logger.info('Assignment started')
                break
