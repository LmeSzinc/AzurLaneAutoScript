from module.base.utils import color_similar, get_color
from module.logger import logger
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_interact import DUNGEON_COMBAT_INTERACT, MAP_LOADING
from tasks.combat.assets.assets_combat_prepare import COMBAT_PREPARE
from tasks.map.assets.assets_map_control import A_BUTTON
from tasks.rogue.assets.assets_rogue_weekly import REWARD_ENTER


class CombatInteract(UI):
    def handle_combat_interact(self, interval=2):
        """
        Returns:
            bool: If clicked.
        """
        if self.appear_then_click(DUNGEON_COMBAT_INTERACT, interval=interval):
            return True

        return False

    def combat_enter_from_map(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_main, DUNGEON_COMBAT_INTERACT
            out: COMBAT_PREPARE
                or REWARD_ENTER
        """
        logger.info('Combat enter from map')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(COMBAT_PREPARE):
                # Confirm page loaded
                if self.image_color_count(COMBAT_PREPARE.button, color=(230, 230, 230), threshold=240, count=400):
                    logger.info(f'At {COMBAT_PREPARE}')
                    break
            # is_page_rogue_main()
            if self.match_template_color(REWARD_ENTER):
                logger.info(f'At rogue {REWARD_ENTER}')
                break
            if self.handle_combat_interact():
                continue

    def is_map_loading(self):
        if self.appear(MAP_LOADING, similarity=0.75):
            return True

        return False

    def is_map_loading_black(self):
        color = get_color(self.device.image, A_BUTTON.area)
        if color_similar(color, (0, 0, 0)):
            return True
        return False
