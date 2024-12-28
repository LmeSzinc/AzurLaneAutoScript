from module.combat.combat import *
from module.combat.combat import QUIT
from module.exercise.assets import *
from module.exercise.equipment import ExerciseEquipment
from module.exercise.hp_daemon import HpDaemon
from module.exercise.opponent import OPPONENT, OpponentChoose
from module.ui.assets import EXERCISE_CHECK


class ExerciseCombat(HpDaemon, OpponentChoose, ExerciseEquipment, Combat):
    def _in_exercise(self):
        return self.appear(EXERCISE_CHECK, offset=(20, 20))

    def _combat_preparation(self, skip_first_screenshot=True):
        logger.info('Combat preparation')
        self.device.stuck_record_clear()
        self.device.click_record_clear()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(BATTLE_PREPARATION, offset=(20, 20), interval=2):
                # self.equipment_take_on()
                pass

                self.device.click(BATTLE_PREPARATION)
                continue

            # End
            pause = self.is_combat_executing()
            if pause:
                logger.attr('BattleUI', pause)
                break

    def _combat_execute(self):
        """
        Returns:
            bool: True if wins. False if quit.
        """
        logger.info('Combat execute')
        self.device.stuck_record_clear()
        self.device.click_record_clear()
        self.low_hp_confirm_timer = Timer(1.5, count=2).start()
        show_hp_timer = Timer(5)
        pause_interval = Timer(0.5, count=1)
        # Pause button to identify battle UI theme
        pause = None
        success = True
        end = False

        while 1:
            self.device.screenshot()

            p = self.is_combat_executing()
            if p:
                if end:
                    end = False
                if pause is None:
                    pause = p
            else:
                self.low_hp_confirm_timer.reset()
                # Finish - S or D rank
                if self.appear_then_click(BATTLE_STATUS_S, interval=1):
                    success = True
                    end = True
                    continue
                if self.appear_then_click(BATTLE_STATUS_D, interval=1):
                    success = True
                    end = True
                    logger.info("Exercise LOST")
                    continue
            if self.appear_then_click(GET_ITEMS_1, interval=1):
                continue
            if self.appear(EXP_INFO_S, interval=1):
                self.device.click(CLICK_SAFE_AREA)
                continue
            if self.appear(EXP_INFO_D, interval=1):
                self.device.click(CLICK_SAFE_AREA)
                continue
            # Last D rank screen
            if self.appear_then_click(OPTS_INFO_D, offset=(30, 30), interval=1):
                success = True
                end = True
                logger.info("Exercise LOST")
                continue

            # Quit
            if self.handle_combat_quit():
                pause_interval.reset()
                success = False
                end = True
                continue
            if self.appear_then_click(QUIT_RECONFIRM, offset=(20, 20), interval=5):
                self.interval_reset(QUIT)
                pause_interval.reset()
                continue
            if not end:
                if p and self._at_low_hp(image=self.device.image, pause=pause):
                    logger.info('Exercise quit')
                    if pause_interval.reached():
                        self.device.click(p)
                        pause_interval.reset()
                        continue
                else:
                    if show_hp_timer.reached():
                        show_hp_timer.reset()
                        self._show_hp()

            # End
            if self._in_exercise() or self.appear(BATTLE_PREPARATION, offset=(20, 20)):
                logger.hr('Combat end')
                if not end:
                    logger.warning('Combat ended without end conditions detected')
                break

        return success

    def _choose_opponent(self, index, skip_first_screenshot=True):
        """
        Args:
            index (int): From left to right. 0 to 3.
        """
        logger.hr('Opponent: %s' % str(index))
        opponent_timer = Timer(5)
        preparation_timer = Timer(5)

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if opponent_timer.reached() and self._in_exercise():
                self.device.click(OPPONENT[index, 0])
                opponent_timer.reset()

            if preparation_timer.reached() and self.appear_then_click(EXERCISE_PREPARATION):
                # self.device.sleep(0.3)
                preparation_timer.reset()
                opponent_timer.reset()
                continue

            # End
            if self.appear(BATTLE_PREPARATION, offset=(20, 20)):
                break

    def _preparation_quit(self):
        logger.info('Preparation quit')
        self.ui_back(check_button=self._in_exercise, appear_button=BATTLE_PREPARATION, skip_first_screenshot=True)

    def _combat(self, opponent):
        """
        Args:
            opponent(int): From left to right. 0 to 3.

        Returns:
            bool: True if wins. False if challenge times exhausted.
        """
        self._choose_opponent(opponent)

        trial = self.config.Exercise_OpponentTrial
        if not isinstance(trial, int) or trial < 1:
            logger.warning(f'Invalid Exercise.OpponentTrial: {trial}, revise to 1')
            self.config.Exercise_OpponentTrial = 1

        for n in range(1, self.config.Exercise_OpponentTrial + 1):
            logger.hr('Try: %s' % n)
            self._combat_preparation()
            success = self._combat_execute()
            if success:
                return success

        self._preparation_quit()
        return False

    def equipment_take_off_when_finished(self):
        if self.config.EXERCISE_FLEET_EQUIPMENT is None:
            return False
        if not self.equipment_has_take_on:
            return False

        self._choose_opponent(0)
        self.equipment_take_off()
        self._preparation_quit()

    def equipment_take_on(self):
        if self.config.EXERCISE_FLEET_EQUIPMENT is None:
            return False
        if self.equipment_has_take_on:
            return False

        self._choose_opponent(0)
        super().equipment_take_on()
        self._preparation_quit()
