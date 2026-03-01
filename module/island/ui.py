from module.base.timer import Timer
from module.handler.assets import MAINTENANCE_ANNOUNCE, USE_DATA_KEY_NOTIFIED
from module.island.assets import *
from module.logger import logger
from module.ui.assets import SHOP_BACK_ARROW
from module.ui.page import page_island_phone
from module.ui.ui import UI


class IslandUI(UI):
    def ui_additional(self, get_ship=True):
        return super().ui_additional(get_ship=False)

    @cached_property
    def _island_season_bottom_navbar(self):
        """
        6 options:
            homepage,
            pt_reward,
            season_task,
            season_shop,
            season_rank,
            season_history
        """
        island_season_bottom_navbar = ButtonGrid(
            origin=(14, 677), delta=(213, 0),
            button_shape=(186, 33), grid_shape=(6, 1),
            name='ISLAND_SEASON_BOTTOM_NAVBAR'
        )
        return Navbar(grids=island_season_bottom_navbar,
                      active_color=(237, 237, 237),
                      inactive_color=(65, 78, 96),
                      active_count=500,
                      inactive_count=500)

    def island_season_bottom_navbar_ensure(self, left=None, right=None):
        """
        Args:
            left (int):
                1 for homepage,
                2 for pt_reward,
                3 for season_task,
                4 for season_shop,
                5 for season_rank,
                6 for season_history
            right (int):
                1 for season_history,
                2 for season_rank,
                3 for season_shop,
                4 for season_task,
                5 for pt_reward,
                6 for homepage

        """
        return self.appear(ISLAND_MANAGEMENT_CHECK, offset=(20, 20), interval=interval)

    def island_in_transport(self, interval=0):
        """
        Args:
            interval (int):

        Returns:
            bool: if in page ISLAND_TRANSPORT_CHECK
        """
        return self.match_template_color(ISLAND_TRANSPORT_CHECK, offset=(20, 20), interval=interval)

    def island_management_enter(self):
        """
        Enter island management page.

        Returns:
            bool: if success

        Pages:
            in: page_island_phone
            out: ISLAND_MANAGEMENT_CHECK
        """
        logger.info('Island management enter')
        self.interval_clear(ISLAND_MANAGEMENT_CHECK)
        if self.appear(ISLAND_MANAGEMENT_LOCKED, offset=(20, 20)):
            return False
        self.ui_click(
            click_button=ISLAND_MANAGEMENT,
            check_button=self.island_in_management,
            offset=(20, 20),
            retry_wait=2,
            skip_first_screenshot=True
        )
        return True

    def island_transport_enter(self):
        """
        Enter island management page.

        Returns:
            bool: if success

        Pages:
            in: page_island_phone
            out: ISLAND_MANAGEMENT_CHECK
        """
        logger.info('Island transport enter')
        self.ui_click(
            click_button=ISLAND_TRANSPORT,
            check_button=self.island_in_transport,
            offset=(20, 20),
            retry_wait=2,
            skip_first_screenshot=True
        )
        return True

    def island_ui_back(self):
        """
        Pages:
            in: any page with SHOP_BACK_ARROW
            out: page_island_phone
        """
        logger.info('Island UI back')
        self.ui_click(
            click_button=SHOP_BACK_ARROW,
            check_button=page_island_phone.check_button,
            offset=(20, 20),
            retry_wait=2,
            skip_first_screenshot=True
        )

    def ui_ensure_management_page(self):
        """
        Pages:
            in: page_island_phone or product page
            out: ISLAND_MANAGEMENT_CHECK
        """
        logger.info('UI ensure management page')
        self.interval_clear(ISLAND_MANAGEMENT_CHECK)
        confirm_timer = Timer(1, count=2).start()
        for _ in self.loop():
            if self.island_in_management():
                if confirm_timer.reached():
                    break
                continue
            else:
                confirm_timer.reset()

            if self.appear_then_click(SHOP_BACK_ARROW, offset=(20, 20), interval=2):
                continue

            if self.appear_then_click(ISLAND_MANAGEMENT, offset=(20, 20), interval=2):
                continue

    def handle_get_items(self):
        if self.appear_then_click(GET_ITEMS_ISLAND, offset=(20, 20), interval=2):
            return True
        return False

    def ui_additional(self, get_ship=True):
        # notify in page_dormmenu
        if self.appear(MAINTENANCE_ANNOUNCE, offset=(100, 50)):
            for _ in self.loop():
                enabled = self.image_color_count(
                    USE_DATA_KEY_NOTIFIED, color=(140, 207, 66), threshold=180, count=10)
                if enabled:
                    break

                if self.appear(MAINTENANCE_ANNOUNCE, offset=(100, 50), interval=5):
                    self.device.click(USE_DATA_KEY_NOTIFIED)
                    continue

            self.interval_clear(MAINTENANCE_ANNOUNCE)
            self.appear_then_click(MAINTENANCE_ANNOUNCE, offset=(100, 50), interval=2)
            return True
        
        # info in page_island
        if self.appear_then_click(ISLAND_INFO_EXIT, offset=(30, 30), interval=3):
            return True

        return super().ui_additional(get_ship=False)
