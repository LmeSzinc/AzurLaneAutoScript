from datetime import timedelta, datetime

from module.equipment.assets import EQUIPMENT_OPEN
from module.exception import ScriptError
from module.logger import logger
from module.notify import handle_notify
from module.os.assets import FLEET_FLAGSHIP
from module.os.map import OSMap
from module.os.ship_exp import ship_info_get_level_exp
from module.os.ship_exp_data import LIST_SHIP_EXP


class OpsiCheckLeveling(OSMap):
    def os_check_leveling(self):
        logger.hr('OS check leveling', level=1)
        logger.attr('OpsiCheckLeveling_LastRun', self.config.OpsiCheckLeveling_LastRun)
        time_run = self.config.OpsiCheckLeveling_LastRun + timedelta(days=1)
        logger.info(f'Task OpsiCheckLeveling run time is {time_run}')
        if datetime.now().replace(microsecond=0) < time_run:
            logger.info('Not running time, skip')
            return
        target_level = self.config.OpsiCheckLeveling_TargetLevel
        if not isinstance(target_level, int) or target_level < 0 or target_level > 125:
            logger.error(f'Invalid target level: {target_level}, must be an integer between 0 and 125')
            raise ScriptError(f'Invalid opsi ship target level: {target_level}')
        if target_level == 0:
            logger.info('Target level is 0, skip')
            return

        logger.attr('Fleet to check', self.config.OpsiFleet_Fleet)
        self.fleet_set(self.config.OpsiFleet_Fleet)
        self.ship_info_enter(FLEET_FLAGSHIP)
        all_full_exp = True

        while 1:
            self.device.screenshot()
            level, exp = ship_info_get_level_exp(main=self)
            current_total_exp = LIST_SHIP_EXP[level - 1] + exp
            logger.info(
                f'Level: {level}, Exp: {exp}, Total Exp: {current_total_exp}, Target Exp: {LIST_SHIP_EXP[target_level - 1]}')
            if current_total_exp < LIST_SHIP_EXP[target_level - 1]:
                all_full_exp = False
                break
            if not self.ship_view_next():
                break

        if all_full_exp:
            logger.info(f'All ships in fleet {self.config.OpsiFleet_Fleet} are full exp, '
                        f'level {target_level} or above')
            handle_notify(
                self.config.Error_OnePushConfig,
                title=f"Alas <{self.config.config_name}> level check passed",
                content=f"<{self.config.config_name}> {self.config.task} reached level limit {target_level} or above."
            )
        self.ui_back(appear_button=EQUIPMENT_OPEN, check_button=self.is_in_map)
        self.config.OpsiCheckLeveling_LastRun = datetime.now().replace(microsecond=0)
        if all_full_exp and self.config.OpsiCheckLeveling_DelayAfterFull:
            logger.info('Delay task after all ships are full exp')
            self.config.task_delay(server_update=True)
            self.config.task_stop()

