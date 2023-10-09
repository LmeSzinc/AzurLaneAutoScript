from module.base.button import ClickButton
from module.base.timer import Timer
from module.base.utils import area_offset
from module.logger import logger
from tasks.base.page import page_rogue
from tasks.map.control.waypoint import ensure_waypoints
from tasks.map.route.base import RouteBase as RouteBase_
from tasks.rogue.assets.assets_rogue_reward import ROGUE_REPORT
from tasks.rogue.assets.assets_rogue_ui import BLESSING_CONFIRM
from tasks.rogue.bleesing.blessing import RogueBlessingSelector
from tasks.rogue.bleesing.bonus import RogueBonusSelector
from tasks.rogue.bleesing.curio import RogueCurioSelector
from tasks.rogue.event.event import RogueEvent
from tasks.rogue.route.exit import RogueExit


class RouteBase(RouteBase_, RogueExit, RogueEvent):
    registered_domain_exit = None

    def combat_expected_end(self):
        if self.is_page_choose_blessing():
            logger.info('Combat ended at is_page_choose_blessing()')
            return True
        if self.is_page_choose_curio():
            logger.info('Combat ended at is_page_choose_curio()')
            return True
        if self.is_page_choose_bonus():
            logger.info('Combat ended at is_page_choose_bonus()')
            return True

        return False

    def combat_execute(self, expected_end=None):
        return super().combat_execute(expected_end=self.combat_expected_end)

    def handle_blessing(self):
        """
        Returns:
            bool: If handled
        """
        if self.is_page_choose_blessing():
            logger.hr('Choose blessing', level=2)
            selector = RogueBlessingSelector(self)
            selector.recognize_and_select()
            return True
        if self.is_page_choose_curio():
            logger.hr('Choose curio', level=2)
            selector = RogueCurioSelector(self)
            selector.recognize_and_select()
            return True
        if self.is_page_choose_bonus():
            logger.hr('Choose bonus', level=2)
            selector = RogueBonusSelector(self)
            selector.recognize_and_select()
            return True
        if self.handle_blessing_popup():
            return True

        return False

    def clear_blessing(self, skip_first_screenshot=True):
        """
        Pages:
            in: combat_expected_end()
            out: is_in_main()
        """
        logger.info('Clear blessing')
        switched = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_main():
                logger.info(f'clear_blessing() ended at page_main')
                if switched:
                    self.wait_until_minimap_stabled()
                break

            if self.handle_blessing():
                switched = True
                continue

    def clear_occurrence(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_rogue, occurrence
            out: is_in_main()
        """
        logger.info('Clear occurrence')
        self.event_title = None
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_main():
                logger.info(f'clear_occurrence() ended at page_main')
                break

            if self.handle_reward(interval=2):
                continue
            if self.is_combat_executing():
                logger.hr('Combat', level=2)
                self.combat_execute()
                continue
            if self.handle_blessing():
                continue
            if self.ui_page_appear(page_rogue):
                if self.handle_event_continue():
                    continue
                if self.handle_event_option():
                    continue

    def _goto(self, *args, **kwargs):
        result = super()._goto(*args, **kwargs)
        if 'enemy' in result:
            self.clear_blessing()
        return result

    def wait_until_minimap_stabled(self):
        logger.info('Wait until minimap stabled')
        radius = self.minimap.MINIMAP_RADIUS
        area = area_offset((-radius, -radius, radius, radius), offset=self.minimap.MINIMAP_CENTER)
        minimap = ClickButton(area, name='MINIMAP')
        self.wait_until_stable(minimap, timeout=Timer(1.5, count=5))

    """
    Additional rogue methods
    """

    def clear_elite(self, *waypoints):
        logger.hr('Clear elite', level=1)
        waypoints = ensure_waypoints(waypoints)
        end_point = waypoints[-1]
        end_point.speed = 'run_2x'

        # TODO: Use techniques before BOSS
        pass

        result = super().clear_enemy(*waypoints)
        return result

    def _domain_event_expected_end(self):
        """
        Returns:
            bool: If entered event
        """
        if self.ui_page_appear(page_rogue):
            return True
        return False

    def clear_event(self, *waypoints):
        """
        Handle an event in DomainOccurrence, DomainEncounter, DomainTransaction
        """
        logger.hr('Clear event', level=1)
        waypoints = ensure_waypoints(waypoints)
        end_point = waypoints[-1]
        end_point.endpoint_threshold = 1.5
        end_point.interact_radius = 7
        end_point.expected_end.append(self._domain_event_expected_end)

        result = self.goto(*waypoints)
        self.clear_occurrence()
        return result

    def domain_reward(self, *waypoints):
        """
        Get reward of the DomainElite and DomainBoss
        """
        logger.hr('Clear reward', level=1)

        # TODO: Skip if user don't want rewards or stamina exhausted
        return []

        result = self.goto(*waypoints)

        # TODO: Get reward
        pass

        return result

    def domain_herta(self, *waypoints):
        """
        Most people don't buy herta shop, skip
        """
        pass

    def _domain_exit_expected_end(self):
        """
        Returns:
            bool: If domain exited
        """
        if self.is_map_loading():
            logger.info('domain exit: is_map_loading()')
            return True
        # No loading after elite
        if self.is_map_loading_black():
            logger.info('domain exit: is_map_loading_black()')
            return True
        # Rogue cleared
        if self.appear(ROGUE_REPORT, interval=2):
            logger.info(f'domain exit: {ROGUE_REPORT}')
            return True

        if self.handle_popup_confirm():
            return False

        return False

    def _domain_exit_wait_next(self, skip_first_screenshot=True):
        """
        Pages:
            in: is_map_loading()
            out: page_main
                or page_rogue if rogue cleared
        """
        logger.info('Wait next domain')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_main():
                logger.info('Entered another domain')
                self.wait_until_minimap_stabled()
                break
            if self.ui_page_appear(page_rogue):
                logger.info('Rogue cleared')
                break

            if self.appear(ROGUE_REPORT, interval=2):
                logger.info(f'{ROGUE_REPORT} -> {BLESSING_CONFIRM}')
                self.device.click(BLESSING_CONFIRM)
                continue
            # Confirm that leave without getting rewards
            if self.handle_popup_confirm():
                continue
            # First-time cleared reward
            if self.handle_reward():
                continue

    def domain_single_exit(self, *waypoints):
        """
        Goto a single exit, exit current domain
        end_rotation is not required
        """
        logger.hr('Domain single exit', level=1)
        waypoints = ensure_waypoints(waypoints)
        end_point = waypoints[-1]
        end_point.interact_radius = 7
        end_point.expected_end.append(self._domain_exit_expected_end)

        result = self.goto(*waypoints)
        self._domain_exit_wait_next()
        return result

    def domain_exit(self, *waypoints, end_rotation=None):
        logger.hr('Domain exit', level=1)
        waypoints = ensure_waypoints(waypoints)
        end_point = waypoints[-1]
        end_point.endpoint_threshold = 1.5
        result = self.goto(*waypoints)

        logger.hr('End rotation', level=2)
        self.rotation_set(end_rotation, threshold=10)

        logger.hr('Find domain exit', level=2)
        direction = self.predict_door_by_name(self.device.image)
        direction_limit = 55
        if direction is not None:
            if abs(direction) > direction_limit:
                logger.warning(f'Unexpected direction to go: {direction}, limited in {direction_limit}')
                if direction > 0:
                    direction = direction_limit
                elif direction < 0:
                    direction = -direction_limit
            end_point.min_speed = 'run'
            end_point.interact_radius = 50
            end_point.expected_end.append(self._domain_exit_expected_end)
            end_point.lock_direction = direction
            self.goto(end_point)
            self._domain_exit_wait_next()

        return result

    """
    Route
    """

    def register_domain_exit(self, *waypoints, end_rotation=None):
        """
        Register an exit, call `domain_exit()` at route end
        """
        self.registered_domain_exit = (waypoints, end_rotation)

    def before_route(self):
        self.registered_domain_exit = None

    def after_route(self):
        if self.registered_domain_exit is not None:
            waypoints, end_rotation = self.registered_domain_exit
            self.domain_exit(*waypoints, end_rotation=end_rotation)
        else:
            logger.info('No domain exit registered')
