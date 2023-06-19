from datetime import datetime, timedelta

from module.base.timer import Timer
from module.logger import logger
from tasks.assignment.assets.assets_assignment_dispatch import *
from tasks.assignment.assets.assets_assignment_ui import DISPATCHED
from tasks.assignment.keywords import *
from tasks.assignment.ui import AssignmentSwitch, AssignmentUI

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

    def dispatch(self, assignment: AssignmentEntry, duration: int):
        """
        Dispatch assignment.
        Should be called only when limit is checked

        Args:
            assignment (AssignmentEntry):
            duration (int): user specified duration

        Pages:
            in: EMPTY_SLOT
            out: DISPATCHED
        """
        self._select_characters()
        self._select_duration(duration)
        self._confirm_assignment(CONFIRM_ASSIGNMENT)
        self.dispatched[assignment] = datetime.now() + \
            timedelta(hours=duration)

    def _select_characters(self):
        """
        Pages:
            in: EMPTY_SLOT
            out: CHARACTER_LIST
        """
        skip_first_screenshot = True
        click_timer = Timer(1, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            if not self.appear(EMPTY_SLOT):
                logger.info('Assignment slots are all filled')
                break
            # Ensure character list
            if not self.appear(CHARACTER_LIST):
                if click_timer.reached_and_reset():
                    self.device.click(EMPTY_SLOT)
                continue
            # Select
            if click_timer.reached_and_reset():
                self.device.click(CHARACTER_1)
                self.device.click(CHARACTER_2)

    def _select_duration(self, duration: int):
        if duration not in {4, 8, 12, 20}:
            logger.warning(
                f'Duration {duration} is out of scope, reset it to 20')
            duration = 20
        ASSIGNMENT_DURATION_SWITCH.set(str(duration), self)

    def _confirm_assignment(self, dispatch_button: ButtonWrapper) -> bool:
        """
        Args:
            dispatch_button (ButtonWrapper): 
                Button to be clicked, CONFIRM_ASSIGNMENT or REDISPATCH

        Pages:
            in: CONFIRM_ASSIGNMENT or REDISPATCH
            out: DISPATCHED
        """
        skip_first_screenshot = True
        counter = Timer(1, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            if self.appear(DISPATCHED) and self.appear(ASSIGNMENT_STARTED_CHECK):
                if counter.reached():
                    logger.info(f'Assignment started')
                    break
                continue
            # Click
            if self.appear(dispatch_button, interval=2):
                self.device.click(dispatch_button)
                counter.reset()
                continue
