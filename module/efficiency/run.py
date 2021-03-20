from module.base.decorator import cached_property
from module.base.utils import ensure_time
from module.logger import logger
from module.reward.reward import Reward


class EfficiencyRun(Reward):
    @cached_property
    def efficiency_rest_interval(self):
        """
        EFFICIENCY_REST_INTERVAL should be string in minutes, such as '20', '10, 40'.
        If it's a time range, should separated with ','

        Returns:
            int: Farm interval in seconds.
        """
        return int(ensure_time(self.config.EFFICIENCY_REST_INTERVAL, precision=3) * 60)

    def efficiency_rest_interval_reset(self):
        """ Call this method after script sleep ends """
        del self.__dict__['efficiency_rest_interval']

    def reward_until_next_session(self):
        logger.hr('Reward until')
        logger.attr('Next_efficiency_session',
                    f'{self.efficiency_rest_interval // 60} min {self.efficiency_rest_interval % 60} sec')
        until_counter = self.efficiency_rest_interval

        while 1:
            if self.config.triggered_app_restart():
                self.app_restart()

            self.reward()

            if until_counter <= 0:
                break
            until_counter -= self.reward_interval
            if until_counter >= 0:
                next_interval = self.reward_interval
            else:
                next_interval = until_counter + self.reward_interval

            logger.attr('Next_reward_exec', f'{next_interval // 60} min {next_interval % 60} sec')
            if self.config.REWARD_STOP_GAME_DURING_INTERVAL:
                interval = ensure_time((10, 30))
                logger.info(f'{self.config.PACKAGE_NAME} will stop in {interval} seconds')
                logger.info('If you are playing by hand, please stop Alas')
                self.device.sleep(interval)
                self.device.app_stop()

            self.device.sleep(next_interval)
            self.reward_interval_reset()
            self.device.stuck_record_clear()

            if self.config.REWARD_STOP_GAME_DURING_INTERVAL:
                self.app_ensure_start()

        self.efficiency_rest_interval_reset()

    def run(self):
        skip_first_run = self.config.EFFICIENCY_SKIP_FIRST_RUN

        while 1:
            if skip_first_run:
                skip_first_run = False
            else:
                backup = self.config.cover(ENABLE_EFFICIENCY=True,
                                           STOP_IF_COUNT_GREATER_THAN=self.config.EFFICIENCY_COUNT)

                if self.config.EFFICIENCY_MODULE == 'main':
                    from module.campaign.run import CampaignRun
                    az = CampaignRun(self.config, device=self.device)
                    az.run(self.config.CAMPAIGN_NAME)
                elif self.config.EFFICIENCY_MODULE == 'event':
                    from module.campaign.run import CampaignRun
                    az = CampaignRun(self.config, device=self.device)
                    az.run(self.config.EVENT_STAGE, folder=self.config.EVENT_NAME)
                else:
                    from module.war_archives.war_archives import CampaignWarArchives
                    az = CampaignWarArchives(self.config, device=self.device)
                    az.run(self.config.WAR_ARCHIVES_STAGE, folder=self.config.WAR_ARCHIVES_NAME)

                backup.recover()

            self.reward_until_next_session()
