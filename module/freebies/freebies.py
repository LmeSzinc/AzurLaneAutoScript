from module.base.base import ModuleBase
from module.freebies.battle_pass import BattlePass
from module.freebies.data_key import DataKey
from module.freebies.mail import Mail
from module.freebies.supply_pack import SupplyPack


class Freebies(ModuleBase):
    def run(self):
        """
        Run all freebie related modules
        """
        if self.config.BattlePass_Collect:
            BattlePass(self.config, self.device).run()

        if self.config.DataKey_Collect:
            DataKey(self.config, self.device).run()

        if self.config.Mail_Collect:
            Mail(self.config, self.device).run()

        if self.config.SupplyPack_Collect:
            SupplyPack(self.config, self.device).run()

        self.config.task_delay(server_update=True)
