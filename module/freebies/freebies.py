from module.base.base import ModuleBase
from module.battle_pass.battle_pass import BattlePass
from module.data_key.data_key import DataKey
from module.mail.mail import Mail
from module.supply_pack.supply_pack import SupplyPack


class Freebies(ModuleBase):
    def run(self):
        """
        Run all freebie related modules
        """
        BattlePass(self.config, self.device).run()
        DataKey(self.config, self.device).run()
        Mail(self.config, self.device).run()
        SupplyPack(self.config, self.device).run()

        self.config.task_delay(server_update=True)

