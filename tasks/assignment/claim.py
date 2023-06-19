from datetime import datetime, timedelta

from module.base.timer import Timer
from module.ocr.ocr import Duration
from tasks.assignment.assets.assets_assignment_claim import *
from tasks.assignment.assets.assets_assignment_dispatch import EMPTY_SLOT
from tasks.assignment.assets.assets_assignment_ui import DISPATCHED
from tasks.assignment.dispatch import AssignmentDispatch
from tasks.assignment.keywords import AssignmentEntry


class AssignmentClaim(AssignmentDispatch):
    def claim(self, assignment: AssignmentEntry, duration_expected: int, should_redispatch: bool):
        """
        Args:
            assignment (AssignmentEntry):
            duration_expected (int): user specified duration
            should_redispatch (bool):

        Pages:
            in: CLAIM
            out: DISPATCHED(succeed) or EMPTY_SLOT(fail)
        """
        redispatched = False
        skip_first_screenshot = True
        counter = Timer(1, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            if self.appear(EMPTY_SLOT) or self.appear(DISPATCHED):
                if counter.reached():
                    break
                continue
            # Claim reward
            if self.appear(CLAIM, interval=2):
                self.device.click(CLAIM)
                continue
            if self.appear(REDISPATCH, interval=2):
                redispatched = should_redispatch and self._is_duration_expected(
                    duration_expected)
                if redispatched:
                    self._confirm_assignment(REDISPATCH)
                    self.dispatched[assignment] = datetime.now(
                    ) + timedelta(hours=duration_expected)
                else:
                    self.device.click(CLOSE_REPORT)
                continue
        # Re-select duration and dispatch
        if should_redispatch and not redispatched:
            self.dispatch(assignment, duration_expected, check_limit=False)

    def _is_duration_expected(self, duration: int) -> bool:
        """
        Check whether duration in assignment report page
        is the same as user specified

        Args:
            duration (int): user specified duration

        Returns:
            bool: If same.
        """
        duration_reported: timedelta = Duration(
            OCR_ASSIGNMENT_REPORT_TIME).ocr_single_line(self.device.image)
        return duration_reported.total_seconds() == duration*3600
