from module.logger import logger
from module.base.base import ModuleBase
from tasks.freebies.support_reward import SupportReward

class Freebies(ModuleBase):
    def run(self):
        """
        Run all freebie tasks
        """
        if self.config.SupportReward_Collect:
            logger.hr('Support Reward')
            SupportReward(config=self.config, device=self.device).run()
            
        self.config.task_delay(server_update=True)