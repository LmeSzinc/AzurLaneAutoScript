from module.campaign.run import CampaignRun
from module.exception import ScriptEnd
from module.logger import logger
from module.raid.raid import Raid, OilExhausted
from module.ui.page import page_raid


class RaidRun(Raid, CampaignRun):
    def run(self, name='', mode='', total=0):
        """
        Args:
            name (str): Raid name, such as 'raid_20200624'
            mode (str): Raid mode, such as 'hard', 'normal', 'easy'
            total (int): Total run count
        """
        logger.hr('Raid', level=1)
        name = name if name else self.config.RAID_NAME
        mode = mode if mode else self.config.RAID_MODE
        if not name or not mode:
            logger.warning(f'RaidRun arguments unfilled. name={name}, mode={mode}')

        self.campaign = self  # A trick to call CampaignRun
        self.campaign_name_set(f'{name}_{mode}')

        self.device.screenshot()

        self.run_count = 0
        while 1:
            if self.handle_app_restart():
                pass
            if self.handle_reward():
                pass

            # End
            if total and self.run_count == total:
                break

            # Log
            if self.config.STOP_IF_COUNT_GREATER_THAN > 0:
                logger.info(f'Count: [{self.run_count}/{self.config.STOP_IF_COUNT_GREATER_THAN}]')
            else:
                logger.info(f'Count: [{self.run_count}]')

            # End
            if self.triggered_stop_condition(oil_check=False):
                break

            # UI ensure
            self.ui_ensure(page_raid)

            # Run
            try:
                self.raid_execute_once(mode=mode if mode else self.config.RAID_MODE, raid=name)
            except OilExhausted:
                self.ui_goto_main()
                break
            except ScriptEnd as e:
                logger.hr('Script end')
                logger.info(str(e))
                break

            # After run
            self.run_count += 1
            if self.config.STOP_IF_COUNT_GREATER_THAN > 0:
                count = self.config.STOP_IF_COUNT_GREATER_THAN - self.run_count
                count = 0 if count < 0 else count
                self.config.config.set('Setting', 'if_count_greater_than', str(count))
                self.config.save()
