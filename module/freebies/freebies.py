from module.base.base import ModuleBase
from module.freebies.battle_pass import BattlePass
from module.freebies.data_key import DataKey
from module.freebies.mail_white import MailWhite
from module.freebies.supply_pack import SupplyPack, SupplyPack_250814
from module.logger import logger


class Freebies(ModuleBase):
    def run(self):
        """
        Run all freebie related modules
        """
        if self.config.BattlePass_Collect:
            logger.hr('Battle pass', level=1)
            BattlePass(self.config, self.device).run()

        if self.config.DataKey_Collect:
            logger.hr('Data key', level=1)
            DataKey(self.config, self.device).run()

        logger.hr('Mail', level=1)
        MailWhite(self.config, self.device).run()

        if self.config.SupplyPack_Collect:
            logger.hr('Supply pack', level=1)
            if self.config.SERVER in ['tw']:
                SupplyPack(self.config, self.device).run()
            else:
                SupplyPack_250814(self.config, self.device).run()

        self.config.task_delay(server_update=True)
