import re
from datetime import datetime

from module.campaign.campaign_status import CampaignStatus
from module.config.config_updater import COALITIONS, EVENTS, GEMS_FARMINGS, HOSPITAL, MARITIME_ESCORTS, RAIDS
from module.config.utils import DEFAULT_TIME
from module.logger import logger
from module.ui.assets import CAMPAIGN_MENU_NO_EVENT
from module.ui.page import page_campaign_menu, page_coalition, page_event, page_sp
from module.war_archives.assets import WAR_ARCHIVES_CAMPAIGN_CHECK


class CampaignEvent(CampaignStatus):
    def _disable_tasks(self, tasks):
        """
        Args:
            tasks (list[str]): Task name
        """
        with self.config.multi_set():
            # Disable normal events
            for task in tasks:
                if task in GEMS_FARMINGS:
                    continue
                keys = f'{task}.Scheduler.Enable'
                logger.info(f'Disable task `{task}`')
                self.config.cross_set(keys=keys, value=False)

            # Reset GemsFarming
            for task in tasks:
                if task not in GEMS_FARMINGS:
                    continue
                name = self.config.cross_get(keys=f'{task}.Campaign.Name', default='2-4')
                if not self.stage_is_main(name):
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
        tasks = EVENTS + RAIDS + COALITIONS + GEMS_FARMINGS + HOSPITAL
        command = self.config.Scheduler_Command
        if limit <= 0 or command not in tasks:
            return False
        if command in GEMS_FARMINGS and self.stage_is_main(self.config.Campaign_Name):
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
        tasks = EVENTS + RAIDS + COALITIONS + MARITIME_ESCORTS + HOSPITAL
        command = self.config.Scheduler_Command
        if command not in tasks or limit == DEFAULT_TIME:
            return False
        if command in GEMS_FARMINGS and self.stage_is_main(self.config.Campaign_Name):
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
        # Check Coin
        if coin == 0:
            # Avoid wrong/zero OCR result
            logger.warning('Coin not found')
            return False
        else:
            if self.is_balancer_task():
                if coin < limit:
                    logger.hr('Reach Coin limit')
                    return True
                else:
                    return False
            else:
                return False

    def handle_task_balancer(self):
        self.config.task_delay(minute=5)
        next_task = self.config.TaskBalancer_TaskCall
        logger.hr(f'TaskBalancer triggered, switching task to {next_task}')
        self.config.task_call(next_task)
        self.config.task_stop()

    def is_event_entrance_available(self):
        """
        Returns:
            bool: True if available

        Raises:
            TaskEnd: If unavailable
        """
        if self.appear(CAMPAIGN_MENU_NO_EVENT, offset=(20, 20)):
            logger.info('Event unavailable, disable task')
            tasks = EVENTS + RAIDS + COALITIONS + GEMS_FARMINGS + HOSPITAL
            self._disable_tasks(tasks)
            self.config.task_stop()
        else:
            logger.info('Event available')
            return True

    def ui_goto_event(self):
        # Already in page_event, skip event_check.
        if self.ui_get_current_page() == page_event:
            if self.appear(WAR_ARCHIVES_CAMPAIGN_CHECK, offset=(20, 20)):
                logger.info('At war archives')
                self.ui_goto_main()
            else:
                logger.info('Already at page_event')
                return True
        self.ui_goto(page_campaign_menu)
        # Check event availability
        if self.is_event_entrance_available():
            self.ui_goto(page_event)
            return True

    def ui_goto_sp(self):
        # Already in page_event, skip event_check.
        if self.ui_get_current_page() == page_sp:
            if self.appear(WAR_ARCHIVES_CAMPAIGN_CHECK, offset=(20, 20)):
                logger.info('At war archives')
                self.ui_goto_main()
            else:
                logger.info('Already at page_sp')
                return True
        self.ui_goto(page_campaign_menu)
        # Check event availability
        if self.is_event_entrance_available():
            self.ui_goto(page_sp)
            return True

    def ui_goto_coalition(self):
        # Already in page_event, skip event_check.
        if self.ui_get_current_page() == page_coalition:
            logger.info('Already at page_coalition')
            return True
        else:
            self.ui_goto(page_campaign_menu)
            # Check event availability
            if self.is_event_entrance_available():
                self.ui_goto(page_coalition)
                return True

    def disable_raid_on_event(self):
        """
        Disable raid tasks (or coalition) when entered an event,
        to be foolproof if user forgot to disable raid tasks when raid is over and another event is ongoing
        """
        command = self.config.Scheduler_Command
        if command not in EVENTS + GEMS_FARMINGS:
            return False
        if command in GEMS_FARMINGS and self.stage_is_main(self.config.Campaign_Name):
            return False

        tasks = RAIDS + COALITIONS + MARITIME_ESCORTS
        tasks = [t for t in tasks if self.config.is_task_enabled(t)]
        if tasks:
            logger.info('New event ongoing, disable old event tasks')
            self._disable_tasks(tasks)
            return True
        else:
            return False

    @staticmethod
    def stage_is_main(name) -> bool:
        """
        Predict if given stage name is a event

        Args:
            name (str): Such as `7-2`, `D3`
        """
        regex_main = re.compile(r'\d{1,2}[-_]\d')
        return bool(regex_main.search(name))
