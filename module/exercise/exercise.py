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

    def _new_opponent(self):
        logger.info('New opponent')
        self.appear_then_click(NEW_OPPONENT)
        self.opponent_change_count += 1
        self.device.sleep(1)

    def _exercise_once(self):
        while self.opponent_change_count <= 5:
            self._opponent_fleet_check_all()
            for opponent in self._opponent_sort():
                success = self._combat(opponent)
                if success:
                    return success
            self._new_opponent()
            self._opponent_fleet_check_all()
        return False

    def run(self):
        self.ui_ensure(page_exercise)
        # self.equipment_take_on()
        # self.device.sleep(1)

        logger.hr('Exercise', level=1)
        while 1:
            self.device.screenshot()
            remain = OCR_EXERCISE_REMAIN.ocr(self.device.image)
            if remain == 0:
                break

            logger.hr('Remain: %s' % remain)
            success = self._exercise_once()
            if not success:
                logger.info('New opponent exhausted')
                break

        self.equipment_take_off_when_finished()

    def record_executed_since(self):
        return self.config.record_executed_since(option=RECORD_OPTION, since=RECORD_SINCE)

    def record_save(self):
        return self.config.record_save(option=RECORD_OPTION)
