from datetime import datetime

from module.logger import logger
from module.ocr.ocr import Duration
from tasks.assignment.assets.assets_assignment_claim import CLAIM
from tasks.assignment.assets.assets_assignment_dispatch import EMPTY_SLOT
from tasks.assignment.assets.assets_assignment_ui import (DISPATCHED,
                                                          OCR_ASSIGNMENT_TIME)
from tasks.assignment.claim import AssignmentClaim
from tasks.assignment.keywords import *
from tasks.base.page import page_assignment, page_menu
from tasks.daily.synthesize import SynthesizeUI


class Assignment(AssignmentClaim, SynthesizeUI):
    def run(self, assignments: list[AssignmentEntry] = None, duration: int = None):
        if assignments is None:
            assignments = [AssignmentEntry.find(
                x.strip()) for x in self.config.Assignment_Filter.split('>')]
        if duration is None:
            duration = self.config.Assignment_Duration

        self.ensure_scroll_top(page_menu)
        self.ui_ensure(page_assignment)
        # Iterate in user-specified order, return undispatched ones
        undispatched = list(self._check_inlist(assignments, duration))
        remain = self._check_all()
        # There are unchecked assignments
        if remain > 0:
            for assignment in undispatched[:remain]:
                self.goto_entry(assignment)
                self.dispatch(assignment, duration)
            if remain < len(undispatched):
                logger.warning('The following assignments can not be dispatched due to limit: '
                               f'{", ".join([x.name for x in undispatched[remain:]])}')
            elif remain > len(undispatched):
                self._dispatch_remain(duration, remain - len(undispatched))

        # Scheduler
        delay = min(self.dispatched.values())
        logger.info(f'Delay assignment check to {str(delay)}')
        self.config.task_delay(target=delay)

    def _check_inlist(self, assignments: list[AssignmentEntry], duration: int):
        """
        Dispatch assignments according to user config

        Args:
            assignments (list[AssignmentEntry]): user specified assignments
            duration (int): user specified duration
        """
        if not assignments:
            return
        logger.hr('Assignment check inlist', level=2)
        logger.info(
            f'User specified assignments: {", ".join([x.name for x in assignments])}')
        _, remain, _ = self._limit_status
        for assignment in assignments:
            self.goto_entry(assignment)
            if self.appear(CLAIM):
                self.claim(assignment, duration, should_redispatch=True)
                continue
            if self.appear(DISPATCHED):
                self.dispatched[assignment] = datetime.now() + Duration(
                    OCR_ASSIGNMENT_TIME).ocr_single_line(self.device.image)
                continue
            if self.appear(EMPTY_SLOT):
                if remain > 0:
                    self.dispatch(assignment, duration)
                    remain -= 1
                else:
                    yield assignment

    def _check_all(self):
        """
        States of assignments from top to bottom are in following order:
            1. Claimable
            2. Dispatched
            3. Dispatchable
        Break when a dispatchable assignment is encountered
        """
        logger.hr('Assignment check all', level=2)
        _, remain, total = self._limit_status
        if total == len(self.dispatched):
            return remain
        for group in self._iter_groups():
            self.goto_group(group)
            entries = self._iter_entries()
            for _ in range(len(group.entries)):
                assignment = next(entries)
                if assignment in self.dispatched:
                    continue
                self.goto_entry(assignment)
                if self.appear(CLAIM):
                    self.claim(assignment, None, should_redispatch=False)
                    remain += 1
                    continue
                if self.appear(DISPATCHED):
                    self.dispatched[assignment] = datetime.now() + Duration(
                        OCR_ASSIGNMENT_TIME).ocr_single_line(self.device.image)
                    continue
                if self.appear(EMPTY_SLOT):
                    break
        return remain

    def _dispatch_remain(self, duration: int, remain: int):
        """
        Dispatch assignments according to preset priority

        Args:
            duration (int): user specified duration
            remain (int): 
                The number of remaining assignments after
                processing the ones specified by user
        """
        if remain <= 0:
            return
        logger.hr('Assignment dispatch remain', level=2)
        logger.warning(f'{remain} remain')
        logger.info(
            'Dispatch remaining assignments according to preset priority')
        group_priority = (
            KEYWORDS_ASSIGNMENT_GROUP.EXP_Materials_Credits,
            KEYWORDS_ASSIGNMENT_GROUP.Character_Materials,
            KEYWORDS_ASSIGNMENT_GROUP.Synthesis_Materials
        )
        for group in group_priority:
            for assignment in group.entries:
                if assignment in self.dispatched:
                    continue
                self.goto_entry(assignment)
                self.dispatch(assignment, duration)
                remain -= 1
                if remain <= 0:
                    return
