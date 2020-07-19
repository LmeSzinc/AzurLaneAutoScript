from module.exercise.assets import *
from module.exercise.combat import ExerciseCombat
from module.logger import logger
from module.ocr.ocr import Digit
from module.ui.ui import page_exercise

OCR_EXERCISE_REMAIN = Digit(OCR_EXERCISE_REMAIN, letter=(173, 247, 74), threshold=128)
RECORD_OPTION = ('DailyRecord', 'exercise')
RECORD_SINCE = (0, 12, 18,)


class Exercise(ExerciseCombat):
    opponent_change_count = 0
    remain = 0

    def _new_opponent(self):
        logger.info('New opponent')
        self.appear_then_click(NEW_OPPONENT)
        self.opponent_change_count += 1
        self.device.sleep(6)

    def _exercise_once(self):
        self._opponent_fleet_check_all()
        for opponent in self._opponent_sort():
            success = self._combat(opponent)
            if success:
                return success
        if self.opponent_change_count <= 5:
            self._new_opponent()
            return True
        return False

    def _exercise_easiest_else_exp(self):
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
                if self.opponent_change_count <= 5:
                    logger.info("Cannot beat calculated easiest opponent, refresh!")
                    self._new_opponent()
                    return True
                else:
                    logger.info("Cannot beat calculated easiest opponent, MAX EXP then!")
                    self.config.EXERCISE_CHOOSE_MODE = "max_exp"
                    restore = self.config.LOW_HP_THRESHOLD
                    self.config.LOW_HP_THRESHOLD = 0

    def run(self):
        # Same day, count set to last known change count or 6 i.e. no refresh
        # New day, count set to 0 i.e. can change up to 5 times
        self.opponent_change_count = self.config.record_day_check()
        logger.info("Change Opponent Count: {}".format(self.opponent_change_count))

        self.ui_ensure(page_exercise)
        # self.equipment_take_on()
        # self.device.sleep(1)

        logger.hr('Exercise', level=1)
        while 1:
            self.device.screenshot()
            self.remain = OCR_EXERCISE_REMAIN.ocr(self.device.image)
            if self.remain == 0:
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
        self.config.record_change_count(value=self.opponent_change_count)
        if not self.remain:
            return self.config.record_save(option=RECORD_OPTION)
        else:
            return self.config.record_save_zero(option=RECORD_OPTION)
