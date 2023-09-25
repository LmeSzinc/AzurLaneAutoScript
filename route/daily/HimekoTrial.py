from module.logger import logger
from tasks.combat.combat import Combat
from tasks.daily.assets.assets_daily_trial import INFO_CLOSE, START_TRIAL
from tasks.daily.trail import CharacterTrial
from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_BackwaterPass
from tasks.map.route.base import RouteBase


class Route(RouteBase, Combat, CharacterTrial):
    def handle_combat_state(self, auto=True, speed_2x=True):
        # No auto in character trial
        auto = False
        return super().handle_combat_state(auto=auto, speed_2x=speed_2x)

    def wait_next_skill(self, expected_end=None, skip_first_screenshot=True):
        # Ended at START_TRIAL
        def combat_end():
            return self.match_template_color(START_TRIAL)

        return super().wait_next_skill(expected_end=combat_end, skip_first_screenshot=skip_first_screenshot)

    def walk_additional(self) -> bool:
        if self.appear_then_click(INFO_CLOSE, interval=2):
            return True
        return super().walk_additional()

    def combat_execute(self, expected_end=None):
        # Battle 1/3
        # Enemy cleared by follow up
        self.wait_next_skill()

        # Battle 2/3
        # Himeko E
        # Rest are cleared by follow up
        self.use_E()
        self.wait_next_skill()

        # Battle 3/3
        # Himeko E
        self.use_E()
        self.wait_next_skill()
        # Herta A, or Natasha A, depends on who wasn't being attacked
        self.use_A()
        self.wait_next_skill()
        # Natasha A, this will also cause weakness break
        # To achieve In_a_single_battle_inflict_3_Weakness_Break_of_different_Types
        self.use_A()
        self.wait_next_skill()
        # Himeko Q
        # To achieve Use_an_Ultimate_to_deal_the_final_blow_1_time
        # May kill the enemy
        self.use_Q(1)
        if not self.wait_next_skill():
            return
        # Herta Q
        # To achieve Use_an_Ultimate_to_deal_the_final_blow_1_time
        # May kill the enemy
        self.use_Q(2)
        if not self.wait_next_skill():
            return

        # Combat should end here, just incase
        logger.warning(f'Himeko trial is not going as expected')
        for _ in range(3):
            self.use_E()
            if not self.wait_next_skill():
                return

    def route_item_enemy(self):
        self.enter_himeko_trial()
        self.map_init(plane=Jarilo_BackwaterPass, position=(519.9, 361.5))

        # Visit 3 items
        self.clear_item(
            Waypoint((587.6, 366.9)).run_2x(),
        )
        self.clear_item(
            Waypoint((575.5, 377.4)),
        )
        self.clear_item(
            # Go through arched door
            Waypoint((581.5, 383.3)).run().set_threshold(3),
            Waypoint((575.7, 417.2)).run(),
        )
        # Goto boss
        self.clear_enemy(
            Waypoint((613.5, 427.3)),
        )

    def route_item(self):
        self.enter_himeko_trial()
        self.map_init(plane=Jarilo_BackwaterPass, position=(519.9, 361.5))

        # Visit 3 items
        self.clear_item(
            Waypoint((587.6, 366.9)).run_2x(),
        )
        self.clear_item(
            Waypoint((575.5, 377.4)),
        )
        self.clear_item(
            # Go through arched door
            Waypoint((581.5, 383.3)).run().set_threshold(3),
            Waypoint((575.7, 417.2)).run(),
        )
        # Exit
        self.exit_trial()

    def route_enemy(self):
        self.enter_himeko_trial()
        self.map_init(plane=Jarilo_BackwaterPass, position=(519.9, 361.5))

        # Goto boss
        self.clear_enemy(
            # Before the corner, turn right
            Waypoint((571.7, 371.3)).run_2x(),
            # Go through arched door
            Waypoint((581.5, 383.3)).run_2x(),
            # Boss
            Waypoint((613.5, 427.3)).run_2x(),
        )

    def exit(self):
        # Fake map_init to expose this method
        # self.map_init(plane=Jarilo_BackwaterPass, position=(519.9, 361.5))
        self.exit_trial_to_main()
