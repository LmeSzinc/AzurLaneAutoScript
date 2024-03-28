import typing as t
from datetime import datetime, timedelta

from module.base.timer import Timer
from module.config.config import Function
from module.config.utils import get_server_next_update
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.ocr.ocr import Digit
from module.os_handler.assets import *
from module.ui.ui import UI
from module.log_res import LogRes

OCR_SHOP_YELLOW_COINS = Digit(SHOP_YELLOW_COINS, letter=(239, 239, 239), threshold=160, name='OCR_SHOP_YELLOW_COINS')
OCR_SHOP_PURPLE_COINS = Digit(SHOP_PURPLE_COINS, letter=(255, 255, 255), name='OCR_SHOP_PURPLE_COINS')


class OSStatus(UI):
    @property
    def is_in_task_explore(self) -> bool:
        return self.config.task.command == 'OpsiExplore'

    @property
    def is_in_task_cl1_leveling(self) -> bool:
        return self.config.task.command == 'OpsiHazard1Leveling'

    @property
    def is_cl1_enabled(self) -> bool:
        return self.config.is_task_enabled('OpsiHazard1Leveling')

    @property
    def nearest_task_cooling_down(self) -> t.Optional[Function]:
        """
        If having any tasks cooling down,
        such as recon scan cooldown and submarine call cooldown.
        """
        now = datetime.now()
        update = get_server_next_update('00:00')
        cd_tasks = [
            'OpsiObscure',
            'OpsiAbyssal',
            'OpsiStronghold',
            'OpsiDaily',
        ]

        def func(task: Function):
            if task.command in cd_tasks and task.enable:
                if task.next_run != update and task.next_run - now <= timedelta(minutes=60):
                    return True

            return False

        tasks = SelectedGrids(self.config.pending_task + self.config.waiting_task).filter(func).sort('next_run')
        return tasks.first_or_none()

    def get_yellow_coins(self, skip_first_screenshot=True) -> int:
        timeout = Timer(2, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            yellow_coins = OCR_SHOP_YELLOW_COINS.ocr(self.device.image)
            if timeout.reached():
                logger.warning('Get yellow coins timeout')
                break

            if yellow_coins < 100:
                # OCR may get 0 or 1 when amount is not immediately loaded
                logger.info('Yellow coins less than 100, assuming it is an ocr error')
                continue
            else:
                break
        LogRes(self.config).YellowCoin = yellow_coins

        return yellow_coins

    def get_purple_coins(self) -> int:
        amount = OCR_SHOP_PURPLE_COINS.ocr(self.device.image)
        LogRes(self.config).PurpleCoin = amount
        return amount
