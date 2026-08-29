import re
from datetime import datetime

from module.campaign.campaign_status import CampaignStatus
from module.config.utils import DEFAULT_TIME
from module.logger import logger
from module.tasks.registry import family_tasks
from module.ui.assets import CAMPAIGN_MENU_NO_EVENT
from module.ui.page import page_campaign_menu, page_coalition, page_event, page_main_white, page_sp
from module.war_archives.assets import WAR_ARCHIVES_CAMPAIGN_CHECK


class CampaignEvent(CampaignStatus):
    def _reset_gems_farming(self, tasks):
        """
        Reset GemsFarming to 2-4 when event is over

        Args:
            tasks (list[str]): Task name
        """
        for task in tasks:
            if task not in family_tasks('gems'):
                continue
            name = self.config.cross_get(keys=f'{task}.Campaign.Name', default='2-4')
            if not self.stage_is_main(name):
                logger.info('Reset GemsFarming to 2-4')
                self.config.cross_set(keys=f'{task}.Campaign.Name', value='2-4')
                self.config.cross_set(keys=f'{task}.Campaign.Event', value='campaign_main')

    def _disable_tasks(self, tasks):
        """
        Args:
            tasks (list[str]): Task name
        """
        with self.config.multi_set():
            # Disable normal events
            for task in tasks:
                if task in family_tasks('gems'):
                    continue
                keys = f'{task}.Scheduler.Enable'
                logger.info(f'Disable task `{task}`')
                self.config.cross_set(keys=keys, value=False)

            # Reset GemsFarming
            self._reset_gems_farming(tasks)

            logger.info('Reset event time limit')
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
            re.sub(r'[,.\'"锛屻€俔', '', str(self.config.EventGeneral_PtLimit))
        )
        tasks = family_tasks('event') + family_tasks('raid') + family_tasks('coalition') + family_tasks('gems') + family_tasks('hospital')
        command = self.config.Scheduler_Command
        if limit <= 0 or command not in tasks:
            return False
        if command in family_tasks('gems') and self.stage_is_main(self.config.Campaign_Name):
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
        tasks = family_tasks('event') + family_tasks('raid') + family_tasks('coalition') + family_tasks('gems') + family_tasks('maritime') + family_tasks('hospital')
        command = self.config.Scheduler_Command
        if command not in tasks or limit == DEFAULT_TIME:
            return False
        if command in family_tasks('gems') and self.stage_is_main(self.config.Campaign_Name):
            return False

        now = datetime.now().replace(microsecond=0)
        logger.attr('Event_time_limit', f'{now} -> {limit}')
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
            tasks = family_tasks('event') + family_tasks('raid') + family_tasks('coalition') + family_tasks('gems') + family_tasks('hospital')
            self._disable_tasks(tasks)
            self.config.task_stop()
        else:
            logger.info('Event available')
            return True

    def event_entrance_ensure(self, pt_icon, offset=(20, 20), page=page_event, log_name=None):
        """Phase 456 D2: shared event-entrance prelude used by per-event
        ui_goto_event implementations.

        Returns:
            bool: True if already at the event page or the entrance is
                  available; None if unavailable (task stopped).
        """
        if self.appear(pt_icon, offset=offset) and self.ui_page_appear(page):
            logger.info(f'Already at {log_name or str(pt_icon)}')
            return True
        self.ui_ensure(page_campaign_menu)
        return self.is_event_entrance_available()

    def event_entrance_click(self, entrance, pt_icon, offset=(20, 20), appear_button=None):
        """Phase 456 D2: single-click entrance (page check on the pt icon)."""
        if appear_button is None:
            appear_button = entrance
        self.ui_click(entrance, check_button=pt_icon, appear_button=appear_button, offset=offset)
        return True

    def event_entrance_from_main(self, detail, detail_white, check_button, entrance, pt_icon,
                                 offset=(40, 20)):
        """Phase 456 D2: main-menu entrance flow (detail panel then entrance).

        Callers navigate to the main page first; the white-background variant
        of the detail button is used when the main page is in white style.
        """
        if self.ui_page_appear(page_main_white):
            self.ui_click(detail_white, check_button=check_button)
        else:
            self.ui_click(detail, check_button=check_button)
        self.ui_click(entrance, check_button=pt_icon, appear_button=check_button, offset=offset)
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
        if command not in family_tasks('event') + family_tasks('gems'):
            return False
        if command in family_tasks('gems') and self.stage_is_main(self.config.Campaign_Name):
            return False

        tasks = family_tasks('raid') + family_tasks('coalition') + family_tasks('maritime')
        tasks = [t for t in tasks if self.config.is_task_enabled(t)]
        if tasks:
            logger.info('New event ongoing, disable old raid event tasks')
            self._disable_tasks(tasks)
            return True
        else:
            return False

    def disable_event_on_raid(self):
        """
        Disable event tasks when entered an raid or coalition,
        to be foolproof if user forgot to disable event tasks when event is over and another raid is ongoing
        """
        command = self.config.Scheduler_Command
        if command not in family_tasks('raid') + family_tasks('coalition') + family_tasks('maritime'):
            return False

        events = [t for t in family_tasks('event') if self.config.is_task_enabled(t)]
        gems = [t for t in family_tasks('gems') if self.config.is_task_enabled(t)]
        with self.config.multi_set():
            if events:
                logger.info('New raid event ongoing, disable old event tasks')
                self._disable_tasks(events)
            if gems:
                self._reset_gems_farming(gems)
        return events or gems

    @staticmethod
    def stage_is_main(name) -> bool:
        """
        Predict if given stage name is a event

        Args:
            name (str): Such as `7-2`, `D3`
        """
        regex_main = re.compile(r'\d{1,2}[-_]\d')
        return bool(regex_main.search(name))
