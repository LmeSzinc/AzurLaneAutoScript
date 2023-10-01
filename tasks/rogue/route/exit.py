from module.logger import logger
from tasks.base.page import page_rogue
from tasks.combat.interact import CombatInteract
from tasks.rogue.assets.assets_rogue_reward import ROGUE_REPORT
from tasks.rogue.assets.assets_rogue_ui import BLESSING_CONFIRM


class RogueExit(CombatInteract):
    def domain_exit_interact(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_main, DUNGEON_COMBAT_INTERACT
            out: page_main
                or page_rogue if rogue cleared
        """
        logger.info(f'Domain exit interact')
        clicked = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if clicked and not self.is_in_main():
                break

            if self.handle_combat_interact():
                clicked = True
                continue
            if self.handle_popup_confirm():
                continue

        logger.info(f'Interact loading')
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_main():
                logger.info('Entered another domain')
                break
            if self.ui_page_appear(page_rogue):
                logger.info('Rogue cleared')
                break

            if self.appear(ROGUE_REPORT, interval=2):
                self.device.click(BLESSING_CONFIRM)
                continue
