from module.base.utils import color_similar, get_color
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_interact import DUNGEON_COMBAT_INTERACT, MAP_LOADING
from tasks.map.assets.assets_map_control import A_BUTTON


class CombatInteract(UI):
    def handle_combat_interact(self):
        """
        Returns:
            bool: If clicked.
        """
        if self.appear_then_click(DUNGEON_COMBAT_INTERACT, interval=2):
            return True

        return False

    def is_map_loading(self):
        if self.appear(MAP_LOADING, similarity=0.75):
            return True

        return False

    def is_map_loading_black(self):
        color = get_color(self.device.image, A_BUTTON.area)
        if color_similar(color, (0, 0, 0)):
            return True
        return False
