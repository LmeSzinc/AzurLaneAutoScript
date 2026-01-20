from module.logger import logger
from module.os.config import OSConfig
from module.os.tasks.abyssal import OpsiAbyssal
from module.os.tasks.archive import OpsiArchive
from module.os.tasks.cross_month import OpsiCrossMonth
from module.os.tasks.daily import OpsiDaily
from module.os.tasks.explore import OpsiExplore
from module.os.tasks.hazard_leveling import OpsiHazard1Leveling
from module.os.tasks.meowfficer_farming import OpsiMeowfficerFarming
from module.os.tasks.month_boss import OpsiMonthBoss
from module.os.tasks.obscure import OpsiObscure
from module.os.tasks.shop import OpsiShop
from module.os.tasks.stronghold import OpsiStronghold
from module.os.tasks.voucher import OpsiVoucher


class OperationSiren(
    OpsiDaily,
    OpsiShop,
    OpsiVoucher,
    OpsiMeowfficerFarming,
    OpsiHazard1Leveling,
    OpsiObscure,
    OpsiAbyssal,
    OpsiArchive,
    OpsiStronghold,
    OpsiMonthBoss,
    OpsiExplore,
    OpsiCrossMonth,
):
    """
    Operation Siren main class that combines all task modules.
    """
    pass


if __name__ == '__main__':
    self = OperationSiren('month_test', task='OpsiMonthBoss')

    self.config = self.config.merge(OSConfig())

    self.device.screenshot()
    self.os_init()

    logger.hr("OS clear Month Boss", level=1)
    self.clear_month_boss()
