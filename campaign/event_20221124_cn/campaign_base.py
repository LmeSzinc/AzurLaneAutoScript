from datetime import datetime

from module.campaign.assets import EVENT_20221124_ENTRANCE, EVENT_20221124_CHECK, EVENT_20250724_CHECK
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.combat.assets import GET_ITEMS_1_RYZA
from module.handler.fast_forward import AUTO_SEARCH
from module.handler.assets import MYSTERY_ITEM
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.ui.page import page_campaign_menu, page_event
from module.war_archives.assets import WAR_ARCHIVES_CAMPAIGN_CHECK


class CampaignBase(CampaignBase_):
    STAGE_INCREASE = [
        'T1 > T2 > T3 > TS1 > T4 > T5',
        'TH1 > TH2 > TH3 > TH4 > TH5',
    ]

    def ui_goto_event_20221124_rerun(self):
        # Already in page_event, skip event_check.
        if self.ui_get_current_page() == page_event:
            if self.appear(WAR_ARCHIVES_CAMPAIGN_CHECK, offset=(20, 20)):
                logger.info('At war archives')
                self.ui_goto_main()
            elif self.appear(EVENT_20250724_CHECK, offset=(20, 20)):
                logger.info('At event 20250724')
                self.ui_goto_main()
            else:
                logger.info('Already at page_event')
                return True
        self.ui_goto(page_campaign_menu)
        # Click new campaign rerun entrance
        self.ui_click(
            click_button=EVENT_20221124_ENTRANCE,
            check_button=EVENT_20221124_CHECK,
            appear_button=EVENT_20221124_ENTRANCE
        )
        return True

    def campaign_set_chapter_event(self, chapter, mode='normal'):
        if chapter.startswith('t'):
            # Time check to activate the `Rerun: The Alchemist and the Archipelago of Secrets` event entrance
            event_rerun_end_datetime = datetime.strptime('2025-08-07 23:59:59', '%Y-%m-%d %H:%M:%S')
            if self.config.start_mtime < event_rerun_end_datetime:
                self.ui_goto_event_20221124_rerun()
            else:
                self.ui_goto_event()
            self.campaign_ensure_chapter(chapter)
            return True

        return super().campaign_set_chapter_event(chapter, mode=mode)

    @staticmethod
    def _campaign_separate_name(name):
        # T, TH, ASP, EX
        if name == 'ex':
            return 't4', '1'
        if name == 'asp':
            return 't3', '1'
        if name == 'sp':
            return 't3', '1'
        if name == 'ts1':
            return 't1', name[-1]
        if name.startswith('th'):
            return 't2', name[-1]
        if name.startswith('t'):
            return 't1', name[-1]

        return CampaignBase_._campaign_separate_name(name)

    @staticmethod
    def _campaign_get_chapter_index(name):
        if name == 't4':
            return 4
        if name == 't3':
            return 3
        if name == 't2':
            return 2
        if name == 't1':
            return 1

        return CampaignBase_._campaign_get_chapter_index(name)

    def campaign_get_entrance(self, name):
        if name == 'sp':
            name = 'asp'
        return super().campaign_get_entrance(name)

    def map_get_info(self):
        name = str(self.config.Campaign_Name).lower()
        super().map_get_info()

        # Chapter TH has no map_percentage and no 3_stars
        if name.startswith('th') or name.startswith('ht'):
            appear = AUTO_SEARCH.appear(main=self)
            self.map_is_100_percent_clear = self.map_is_3_stars = self.map_is_threat_safe = appear
            self.map_has_clear_mode = appear
            self.map_show_info()

    def handle_mystery_items(self, button=None, drop=None):
        # Handle a different GET_ITEMS_1
        if super().handle_mystery_items(button, drop=drop):
            return True
        if self.appear(GET_ITEMS_1_RYZA, offset=(20, 20)):
            logger.attr('Mystery', 'Get item')
            if drop:
                drop.add(self.device.image)
            self.device.click(MYSTERY_ITEM)
            self.device.sleep(0.5)
            self.device.screenshot()
            # self.strategy_close()
            return True
        return False

    def clear_map_items(self, grids):
        """

        Args:
            grids (GridInfo, list[GridInfo]): Grid object or a list of them

        Returns:

        """
        if not isinstance(grids, list):
            grids = [grids]
        grids = SelectedGrids(grids).sort('cost')
        for grid in grids:
            logger.hr('Clear map item')
            logger.info(f'Clear map item on {grid}')
            self.goto(grid)
