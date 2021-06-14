from datetime import datetime

from module.exercise.assets import *
from module.exercise.combat import ExerciseCombat
from module.logger import logger
from module.ocr.ocr import Digit
from module.ui.ui import page_exercise

OCR_EXERCISE_REMAIN = Digit(OCR_EXERCISE_REMAIN, letter=(173, 247, 74), threshold=128)
RECORD_OPTION = ('DailyRecord', 'exercise')
RECORD_COUNT = ('DailyRecord', 'exercise_count')
RECORD_SINCE = (0, 12, 18,)


class Exercise(ExerciseCombat):
    opponent_change_count = 0
    remain = 0

    def _new_opponent(self):
        logger.info('New opponent')
        self.appear_then_click(NEW_OPPONENT)
        self.opponent_change_count += 1

        logger.attr("Change_opponent_count", self.opponent_change_count)
        self.config.config.set(*RECORD_COUNT, str(self.opponent_change_count))
        self.config.save()

        self.ensure_no_info_bar(timeout=3)

    def _opponent_fleet_check_all(self):
        if self.config.EXERCISE_CHOOSE_MODE != 'leftmost':
            super()._opponent_fleet_check_all()

    def _opponent_sort(self):
        if self.config.EXERCISE_CHOOSE_MODE != 'leftmost':
            return super()._opponent_sort()
        else:
            return [0, 1, 2 ,3]

    def _exercise_once(self):
        """Execute exercise once.

        This method handles exercise refresh and exercise failure.

        Returns:
            bool: True if success to defeat one opponent. False if failed to defeat any opponent and refresh exhausted.
        """
        self._opponent_fleet_check_all()
        while 1:
            for opponent in self._opponent_sort():
                success = self._combat(opponent)
                if success:
                    return success

            if self.opponent_change_count >= 5:
                return False

            self._new_opponent()
            self._opponent_fleet_check_all()

    def _exercise_easiest_else_exp(self):
        """Try easiest first, if unable to beat easiest opponent then switch to max exp opponent and accept the loss.

        This method handles exercise refresh and exercise failure.

        Returns:
            bool: True if success to defeat one opponent. False if failed to defeat any opponent and refresh exhausted.
        """
        restore = 0
        self._opponent_fleet_check_all()
        while 1:
            opponents = self._opponent_sort()
            success = self._combat(opponents[0])
            if success:
                self.config.EXERCISE_CHOOSE_MODE = "easiest_else_exp"
                self.config.LOW_HP_THRESHOLD = restore if not self.config.LOW_HP_THRESHOLD else self.config.LOW_HP_THRESHOLD
                return success
            else:
                if self.opponent_change_count < 5:
                    logger.info("Cannot beat calculated easiest opponent, refresh")
                    self._new_opponent()
                    self._opponent_fleet_check_all()
                    continue
                else:
                    logger.info("Cannot beat calculated easiest opponent, MAX EXP then")
                    self.config.EXERCISE_CHOOSE_MODE = "max_exp"
                    restore = self.config.LOW_HP_THRESHOLD
                    self.config.LOW_HP_THRESHOLD = 0

    def _get_opponent_change_count(self):
        """
        Same day, count set to last known change count or 6 i.e. no refresh
        New day, count set to 0 i.e. can change up to 5 times

        Returns:
            int:
        """
        record = datetime.strptime(self.config.config.get(*RECORD_OPTION), self.config.TIME_FORMAT)
        update = self.config.get_server_last_update(RECORD_SINCE)
        if record.date() == update.date():
            # Same Day
            return self.config.config.getint(*RECORD_COUNT, fallback=6)
        else:
            # New Day
            return 0

    def run(self):
        self.ui_ensure(page_exercise)

        logger.hr('Exercise', level=1)
        self.opponent_change_count = self._get_opponent_change_count()
        logger.attr("Change_opponent_count", self.opponent_change_count)
        while 1:
            self.device.screenshot()
            self.remain = OCR_EXERCISE_REMAIN.ocr(self.device.image)
            if self.remain <= self.config.EXERCISE_PRESERVE:
                break

            logger.hr('Remain: %s' % self.remain)
            if self.config.EXERCISE_CHOOSE_MODE == "easiest_else_exp":
                success = self._exercise_easiest_else_exp()
            else:
                success = self._exercise_once()
            if not success:
                logger.info('New opponent exhausted')
                break

        self.equipment_take_off_when_finished()

    def record_executed_since(self):
        return self.config.record_executed_since(option=RECORD_OPTION, since=RECORD_SINCE)

    def record_save(self):
        self.config.config.set(*RECORD_COUNT, str(self.opponent_change_count))
        if self.remain <= self.config.EXERCISE_PRESERVE or self.opponent_change_count >= 5:
            return self.config.record_save(option=RECORD_OPTION)
        else:
            self.config.save()
