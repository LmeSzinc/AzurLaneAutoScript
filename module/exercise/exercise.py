from datetime import timedelta
from module.config.utils import get_server_last_update
from module.exercise.assets import *
from module.exercise.combat import ExerciseCombat
from module.logger import logger
from module.ocr.ocr import Digit, Ocr, OcrYuv
from module.ui.ui import page_exercise


class DatedDuration(Ocr):
    def __init__(self, buttons, lang='cnocr', letter=(255, 255, 255), threshold=128, alphabet='0123456789:IDS天日d',
                 name=None):
        super().__init__(buttons, lang=lang, letter=letter, threshold=threshold, alphabet=alphabet, name=name)

    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('I', '1').replace('D', '0').replace('S', '5')
        return result
    
    def ocr(self, image, direct_ocr=False):
        """
        Do OCR on a dated duration, such as `10d 01:30:30` or `7日01:30:30`.
        
        Args:
            image:
            direct_ocr:
            
        Returns:
            list, datetime.timedelta: timedelta object, or a list of it.
        """
        result_list = super().ocr(image, direct_ocr=direct_ocr)
        if not isinstance(result_list, list):
            result_list = [result_list]
        result_list = [self.parse_time(result) for result in result_list]
        if len(self.buttons) == 1:
            result_list = result_list[0]
        return result_list
    
    @staticmethod
    def parse_time(string):
        """
        Args: 
            string (str): `10d 01:30:30` or `7日01:30:30`
        
        Returns:
            datetime.timedelta:
        """
        import re
        result = re.search(r'(\d{1,2})\D?(\d{1,2}):?(\d{2}):?(\d{2})', string)
        if result:
            result = [int(s) for s in result.groups()]
            return timedelta(days=result[0], hours=result[1], minutes=result[2], seconds=result[3])
        else:
            logger.warning(f'Invalid dated duration: {string}')
            return timedelta(days=0, hours=0, minutes=0, seconds=0)
        

class DatedDurationYuv(DatedDuration, OcrYuv):
    pass


OCR_EXERCISE_REMAIN = Digit(OCR_EXERCISE_REMAIN, letter=(173, 247, 74), threshold=128)
OCR_PERIOD_REMAIN = DatedDuration(OCR_PERIOD_REMAIN, letter=(255, 255, 255), threshold=128)
ADMIRAL_TRIAL_HOUR_INTERVAL = {
    "sun18": [6, 0],
    "sun12": [12, 6],
    "sun0": [24, 12],
    "sat18": [30, 24],
    "sat12": [36, 30],
    "sat0": [48, 36],
    "fri18": [56, 48]
}


class Exercise(ExerciseCombat):
    opponent_change_count = 0
    remain = 0

    def _new_opponent(self):
        logger.info('New opponent')
        self.appear_then_click(NEW_OPPONENT)
        self.opponent_change_count += 1

        logger.attr("Change_opponent_count", self.opponent_change_count)
        self.config.set_record(Exercise_OpponentRefreshValue=self.opponent_change_count)

        self.ensure_no_info_bar(timeout=3)

    def _opponent_fleet_check_all(self):
        if self.config.Exercise_OpponentChooseMode != 'leftmost':
            super()._opponent_fleet_check_all()

    def _opponent_sort(self, method=None):
        if method is None:
            method = self.config.Exercise_OpponentChooseMode
        if method != 'leftmost':
            return super()._opponent_sort(method=method)
        else:
            return [0, 1, 2, 3]

    def _exercise_once(self):
        """Execute exercise once.

        This method handles exercise refresh and exercise failure.

        Returns:
            bool: True if success to defeat one opponent. False if failed to defeat any opponent and refresh exhausted.
        """
        self._opponent_fleet_check_all()
        while 1:
            for opponent in self._opponent_sort():
                logger.hr(f'Opponent {opponent}', level=2)
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
        method = "easiest_else_exp"
        restore = self.config.Exercise_LowHpThreshold
        threshold = self.config.Exercise_LowHpThreshold
        self._opponent_fleet_check_all()
        while 1:
            opponents = self._opponent_sort(method=method)
            logger.hr(f'Opponent {opponents[0]}', level=2)
            self.config.override(Exercise_LowHpThreshold=threshold)
            success = self._combat(opponents[0])
            if success:
                self.config.override(Exercise_LowHpThreshold=restore)
                return success
            else:
                if self.opponent_change_count < 5:
                    logger.info("Cannot beat calculated easiest opponent, refresh")
                    self._new_opponent()
                    self._opponent_fleet_check_all()
                    continue
                else:
                    logger.info("Cannot beat calculated easiest opponent, MAX EXP then")
                    method = "max_exp"
                    threshold = 0

    def _get_opponent_change_count(self):
        """
        Same day, count set to last known change count or 6 i.e. no refresh
        New day, count set to 0 i.e. can change up to 5 times

        Returns:
            int:
        """
        record = self.config.Exercise_OpponentRefreshRecord
        update = get_server_last_update('00:00')
        if record.date() == update.date():
            # Same Day
            return self.config.Exercise_OpponentRefreshValue
        else:
            # New Day
            self.config.set_record(Exercise_OpponentRefreshValue=0)
            return 0


    def server_support_ocr_reset_remain(self) -> bool:
        return self.config.SERVER in ['jp']

   
    def _get_exercise_reset_remain(self):
        """
        Returns:
            datetime.timedelta
        """
        result = OCR_PERIOD_REMAIN.ocr(self.device.image)
        return result

    def run(self):
        self.ui_ensure(page_exercise)

        self.opponent_change_count = self._get_opponent_change_count()
        logger.attr("Change_opponent_count", self.opponent_change_count)

        if not self.server_support_ocr_reset_remain():
            logger.info(f'Server {self.config.SERVER} does not yet support OCR exercise reset remain time')
            logger.info('Please contact the developer to improve as soon as possible')
            remain_time = timedelta(days=0)
        else:
            remain_time = OCR_PERIOD_REMAIN.ocr(self.device.image)
    
        backup = None
        if self.config.Exercise_ExercisePreserve == 5 and remain_time:
            admiral_start, admiral_end = ADMIRAL_TRIAL_HOUR_INTERVAL[self.config.Exercise_AdmiralTrialTime]
            
            if admiral_start > int(remain_time.total_seconds() // 3600) >= admiral_end: #set time for getting admiral
                logger.hr(f'Reach set time for admiral trial, using all attempts.')
                backup = self.config.temporary(
                    Exercise_ExercisePreserve=0
                )    
            elif int(remain_time.total_seconds() // 3600) < 6: #if not set to "sun18", still depleting at sunday 18pm.
                logger.hr(f'Exercise period remain less than 6 hours, using all attempts.')
                backup = self.config.temporary(
                    Exercise_ExercisePreserve=0
                )    

        while 1:
            self.remain = OCR_EXERCISE_REMAIN.ocr(self.device.image)
            if self.remain <= self.config.Exercise_ExercisePreserve:
                break

            logger.hr(f'Exercise remain {self.remain}', level=1)
            if self.config.Exercise_OpponentChooseMode == "easiest_else_exp":
                success = self._exercise_easiest_else_exp()
            else:
                success = self._exercise_once()
            if not success:
                logger.info('New opponent exhausted')
                break
        
        # Restore user settings if necessary after admiral trial.
        if backup is not None:
            backup.recover()

        # self.equipment_take_off_when_finished()

        # Scheduler
        with self.config.multi_set():
            self.config.set_record(Exercise_OpponentRefreshValue=self.opponent_change_count)
            if self.remain <= self.config.Exercise_ExercisePreserve or self.opponent_change_count >= 5:
                self.config.task_delay(server_update=True)
            else:
                self.config.task_delay(success=False)
