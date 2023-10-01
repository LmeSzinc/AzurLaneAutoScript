from module.logger import logger
from tasks.map.control.waypoint import ensure_waypoints
from tasks.map.route.base import RouteBase as RouteBase_
from tasks.rogue.bleesing.blessing import RogueBlessingSelector
from tasks.rogue.bleesing.bonus import RogueBonusSelector
from tasks.rogue.bleesing.curio import RogueCurioSelector
from tasks.rogue.bleesing.ui import RogueUI
from tasks.rogue.route.exit import RogueExit


class RouteBase(RouteBase_, RogueUI, RogueExit):
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

    def clear_blessing(self, skip_first_screenshot=True):
        """
        Pages:
            in: combat_expected_end()
            out: is_in_main()
        """
        logger.info(f'Clear blessing')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_main():
                logger.info(f'clear_blessing() ended at page_main')
                break

            if self.is_page_choose_blessing():
                logger.hr('Choose blessing', level=2)
                selector = RogueBlessingSelector(self)
                selector.recognize_and_select()
            if self.is_page_choose_curio():
                logger.hr('Choose curio', level=2)
                selector = RogueCurioSelector(self)
                selector.recognize_and_select()
            if self.is_page_choose_bonus():
                logger.hr('Choose bonus', level=2)
                selector = RogueBonusSelector(self)
                selector.recognize_and_select()

    """
    Additional rogue methods
    """

    def clear_enemy(self, *waypoints):
        logger.hr('Clear enemy', level=1)
        result = super().clear_enemy(*waypoints)

        self.clear_blessing()
        return result

    def clear_elite(self, *waypoints):
        logger.hr('Clear elite', level=1)
        waypoints = ensure_waypoints(waypoints)
        end_point = waypoints[-1]
        end_point.speed = 'run_2x'

        # Use skill
        pass

        result = super().clear_enemy(*waypoints)

        self.clear_blessing()
        return result

    def clear_event(self, *waypoints):
        """
        Handle an event in DomainOccurrence, DomainEncounter, DomainTransaction
        """
        logger.hr('Clear event', level=1)

        result = self.goto(*waypoints)
        return result

    def domain_reward(self, *waypoints):
        """
        Get reward of the DomainElite and DomainBoss
        """
        logger.hr('Clear reward', level=1)

        # Skip if not going to get reward
        pass

        result = self.goto(*waypoints)
        return result

    def domain_herta(self, *waypoints):
        """
        Most people don't buy herta shop, skip
        """
        pass

    def domain_single_exit(self, *waypoints):
        """
        Goto a single exit, exit current domain
        end_rotation is not required
        """
        logger.hr('Domain single exit', level=1)
        waypoints = ensure_waypoints(waypoints)
        result = self.goto(*waypoints)

        self.domain_exit_interact()
        return result

    def domain_exit(self, *waypoints, end_rotation=None):
        logger.hr('Domain exit', level=1)
        waypoints = ensure_waypoints(waypoints)
        end_point = waypoints[-1]
        end_point.end_rotation = end_rotation
        result = self.goto(*waypoints)

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
