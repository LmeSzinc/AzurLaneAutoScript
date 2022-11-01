import re
from datetime import datetime

from module.campaign.campaign_status import CampaignStatus
from module.config.utils import DEFAULT_TIME
from module.logger import logger


class CampaignEvent(CampaignStatus):
    def _disable_tasks(self, tasks):
        """
        Args:
            tasks (list[str]): Task name
        """
        with self.config.multi_set():
            for task in tasks:
                keys = f'{task}.Scheduler.Enable'
                logger.info(f'Disable task `{task}`')
                self.config.cross_set(keys=keys, value=False)

            for task in ['GemsFarming']:
                if self.config.cross_get(keys=f'{task}.Campaign.Event', default='campaign_main') != 'campaign_main':
                    logger.info(f'Reset GemsFarming to 2-4')
                    self.config.cross_set(keys=f'{task}.Campaign.Name', value='2-4')
                    self.config.cross_set(keys=f'{task}.Campaign.Event', value='campaign_main')

            logger.info(f'Reset event time limit')
            self.config.cross_set(keys='EventGeneral.EventGeneral.TimeLimit', value=DEFAULT_TIME)

    def event_pt_limit_triggered(self):
        """
        Returns:
            bool:

        Pages:
            in: page_event or page_sp
        """
        # Some may use "100,000"
        limit = int(
            re.sub(r'[,.\'"，。]', '', str(self.config.EventGeneral_PtLimit))
        )
        tasks = [
            'Event',
            'Event2',
            'EventA',
            'EventB',
            'EventC',
            'EventD',
            'EventSp',
            'Raid',
            'RaidDaily',
            'GemsFarming',
        ]
        command = self.config.Scheduler_Command
        if limit <= 0 or command not in tasks:
            return False
        if command == 'GemsFarming' and self.config.Campaign_Event == 'campaign_main':
            return False

        pt = self.get_event_pt()
        logger.attr('Event_PT_limit', f'{pt}/{limit}')
        if pt >= limit:
            logger.hr(f'Reach event PT limit: {limit}')
            self._disable_tasks(tasks)
            return True
        else:
            return False

    def event_time_limit_triggered(self):
        """
        Returns:
            bool:

        Pages:
            in: page_event or page_sp
        """
        limit = self.config.EventGeneral_TimeLimit
        tasks = [
            'Event',
            'Event2',
            'EventA',
            'EventB',
            'EventC',
            'EventD',
            'EventSp',
            'GemsFarming',
            'Raid',
            'RaidDaily',
            'MaritimeEscort',
        ]
        command = self.config.Scheduler_Command
        if command not in tasks or limit == DEFAULT_TIME:
            return False
        if command == 'GemsFarming' and self.config.Campaign_Event == 'campaign_main':
            return False

        now = datetime.now().replace(microsecond=0)
        logger.attr('Event_PT_limit', f'{now} -> {limit}')
        if now > limit:
            logger.hr(f'Reach event time limit: {limit}')
            self._disable_tasks(tasks)
            return True
        else:
            return False

    def triggered_task_balancer(self):
        """
        Returns:
            bool: If triggered task_call
        Pages:
            in: page_event or page_sp
        """
        limit = self.config.TaskBalancer_CoinLimit
        coin = self.get_coin()
        tasks = [
            'Event',
            'Event2',
            'Raid',
            'GemsFarming',
        ]
        command = self.config.Scheduler_Command
        # Check Coin
        if coin < limit:
            if command in tasks:
                if self.config.Campaign_Event == 'campaign_main':
                    return False
                else:
                    logger.hr('Triggered task balancer: Coin limit')
                    return True
        else:
            return False

    def handle_task_balancer(self):
        if self.config.TaskBalancer_Enable and self.triggered_task_balancer():
            self.config.task_delay(minute=5)
            next_task = self.config.TaskBalancer_TaskCall
            self.config.task_call(next_task)
            self.config.task_stop()
