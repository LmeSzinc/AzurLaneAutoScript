from datetime import timedelta

from module.config.stored.classes import now
from module.logger import logger
from module.ocr.ocr import Duration
from tasks.assignment.assets.assets_assignment_claim import *
from tasks.assignment.dispatch import AssignmentDispatch
from tasks.assignment.keywords import AssignmentEntry
from tasks.base.page import page_assignment


class AssignmentClaim(AssignmentDispatch):
    def claim(self, assignment: AssignmentEntry, duration_expected: int, should_redispatch: bool):
        """
        Args:
            assignment (AssignmentEntry):
            duration_expected (int): user specified duration
            should_redispatch (bool):

        Pages:
            in: CLAIM
            out: DISPATCHED or EMPTY_SLOT
        """
        redispatched = False
        self._wait_for_report()
        if should_redispatch:
            redispatched = self._is_duration_expected(duration_expected)
        self._exit_report(redispatched)
        if redispatched:
            self._wait_until_assignment_started()
            future = now() + timedelta(hours=duration_expected)
            logger.info(f'Assignment redispatched, will finish at {future}')
            self.dispatched[assignment] = future
            self.has_new_dispatch = True
        elif should_redispatch:
            # Re-select duration and dispatch
            self.goto_entry(assignment)
            self.dispatch(assignment, duration_expected)

    def _wait_for_report(self):
        """
        Pages:
            in: CLAIM
            out: REPORT
        """
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            # Neither CLOSE_REPORT nor REDISPATCH is shown
            # If it is an EVENT assignment
            if self.appear(REPORT):
                logger.info('Assignment report appears')
                break
            # Claim rewards
            if self.appear_then_click(CLAIM, interval=2):
                continue

    def _exit_report(self, should_redispatch: bool):
        """
        Args:
            should_redispatch (bool): determined by user config and duration in report

        Pages:
            in: REPORT
            out: page_assignment
        """
        click_button = REDISPATCH if should_redispatch else CLOSE_REPORT
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            if self.appear(page_assignment.check_button):
                logger.info('Assignment report is closed')
                break
            # Close report
            if self.appear(REPORT, interval=2):
                self.device.click(click_button)
                continue

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
        return duration_reported.total_seconds() == duration * 3600
