import module.config.server as server
from module.logger import logger
from module.private_quarters.assets import *
from module.private_quarters.interact import PQInteract
from module.private_quarters.shop import PQShop
from module.ui.page import page_private_quarters


class PrivateQuarters(PQInteract, PQShop):
    def _pq_shop_enter(self):
        """
        Execute shop enter routine
        """
        # Enter shop
        self.ui_click(
            click_button=PRIVATE_QUARTERS_SHOP_ENTER,
            check_button=PRIVATE_QUARTERS_SHOP_CHECK,
            appear_button=page_private_quarters.check_button,
            offset=(20, 20),
            skip_first_screenshot=True
        )

        # Transition to Sirius section
        self.shop_left_navbar_ensure(2)

        # Transition to Gift section
        self.shop_bottom_navbar_ensure(2)

    def _pq_shop_exit(self):
        """
        Execute shop exit routine
        """
        self.ui_click(
            click_button=PRIVATE_QUARTERS_SHOP_BACK,
            check_button=page_private_quarters.check_button,
            appear_button=PRIVATE_QUARTERS_SHOP_CHECK,
            offset=(20, 20),
            skip_first_screenshot=True
        )

    def pq_shop_weekly_items(self):
        """
        Execute purchase weekly items from shop routine
        For roses, must have 24K+, try next day if low
        For cake, must have 210+, try next day if low
        All other items do not stack so just compares
        against actual price
        """
        logger.hr(f'Get Weekly Items', level=2)

        # Enter shop
        self._pq_shop_enter()

        # Execute buy
        self.shop_buy()

        # Exit shop
        self._pq_shop_exit()

    def pq_execute_interact(self, target_ship):
        """
        Execute interaction sequence with
        target ship girl

        Args:
            target_ship (str):
        """
        # Verify target is a valid selectable
        target_title = target_ship.title().replace('_', ' ')
        if target_ship not in self.available_targets:
            logger.error(f'Unsupported target ship: {target_title}, cannot continue subtask')
            return

        # Handle if target is not in initial load
        # Limit to 3 tries
        if not self.pq_goto_room(target_ship, retry=3):
            return

        # Execute 'interact' routine
        self.pq_interact()

    def pq_run(self, target_interact, target_ship):
        """
        Execute daily private quarters routine
        - Purchase weekly roses from shop
        - Interact with target ship girl

        Args:
            target_interact (bool):
            target_ship     (str):
        """
        logger.hr(f'Private Quarters Run', level=1)
        target_title = target_ship.title().replace('_', ' ')
        logger.info(f'Task configured for Item_Filter={self.shop_filter}, '
                    f'Interact_ShipGirl={target_interact}, '
                    f'Target_ShipGirl={target_title}')

        # Enter shop and buy weekly items (if any)
        if self.shop_filter:
            self.pq_shop_weekly_items()

        # Interact with target if enabled
        if target_interact:
            # Pull count here, exit run if = 0
            count = self.status_get_daily_count()
            if count == 0:
                logger.info('Daily intimacy count exhausted, exit subtask')
                return

            # Able to interact with target, execute
            self.pq_execute_interact(target_ship)

    def run(self):
        """
        Pages:
            in: Any page
            out: page_main, may have info_bar
        """
        if server.server in ['cn', 'en', 'jp']:
            self.ui_goto(page_private_quarters, get_ship=False)
            self.handle_info_bar()

            self.pq_run(
                target_interact=self.config.PrivateQuarters_TargetInteract,
                target_ship=self.config.PrivateQuarters_TargetShip
            )
        else:
            logger.info(f'Private Quarters task not presently supported for {server.server} server.')
            logger.info('If want to address, review necessary assets, replace, update above condition, and test')

        self.config.task_delay(server_update=True)
