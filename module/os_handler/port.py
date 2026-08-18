from module.logger import logger
from module.os_handler.assets import *  # noqa: F403  (data-bundle star import)
from module.os_shop.assets import PORT_SUPPLY_CHECK
from module.os_shop.shop import OSShop

# Azur Lane ports have PORT_GOTO_MISSION, PORT_GOTO_SUPPLY, PORT_GOTO_DOCK.
# Red axis ports have PORT_GOTO_SUPPLY.
# Use PORT_GOTO_SUPPLY as checker.
PORT_CHECK = PORT_GOTO_SUPPLY


class PortHandler(OSShop):
    def port_enter(self):
        """
        Pages:
            in: IN_MAP
            out: PORT_CHECK
        """
        logger.info("Port enter")
        for _ in self.loop():
            if self.appear(PORT_CHECK, offset=(20, 20)):
                break
            if self.appear_then_click(PORT_ENTER, offset=(20, 20), interval=5):
                continue
            if self.handle_map_event():
                continue
        # Buttons at the bottom has an animation to show
        pass  # Already ensured in ui_click

    def port_quit(self, skip_first_screenshot=True):
        """
        Pages:
            in: PORT_CHECK
            out: IN_MAP
        """
        logger.info("Port quit")
        self.ui_back(appear_button=PORT_CHECK, check_button=self.is_in_map, skip_first_screenshot=skip_first_screenshot)
        # Buttons at the bottom has an animation to show
        self.wait_os_map_buttons()


    def port_shop_enter(self):
        """
        Pages:
            in: PORT_CHECK
            out: PORT_SUPPLY_CHECK
        """
        self.ui_click(
            PORT_GOTO_SUPPLY, appear_button=PORT_CHECK, check_button=PORT_SUPPLY_CHECK, skip_first_screenshot=True
        )
        # Port items has an animation to show
        self.device.sleep(0.5)
        self.device.screenshot()

    def port_shop_quit(self):
        """
        Pages:
            in: PORT_SUPPLY_CHECK
            out: PORT_CHECK
        """
        self.ui_back(appear_button=PORT_SUPPLY_CHECK, check_button=PORT_CHECK, skip_first_screenshot=True)

    def port_dock_repair(self):
        """
        Repair all ships.

        Pages:
            in: PORT_CHECK
            out: PORT_CHECK
        """
        self.ui_click(
            PORT_GOTO_DOCK, appear_button=PORT_CHECK, check_button=PORT_DOCK_CHECK, skip_first_screenshot=True
        )

        repaired = False
        for _ in self.loop():
            # End
            if self.info_bar_count():
                break
            if repaired and self.appear(PORT_DOCK_CHECK, offset=(20, 20)):
                break

            # PORT_DOCK_CHECK is button to repair all.
            if self.appear_then_click(PORT_DOCK_CHECK, offset=(20, 20), interval=2):
                continue
            if self.handle_popup_confirm("DOCK_REPAIR"):
                repaired = True
                continue

        self.ui_back(appear_button=PORT_DOCK_CHECK, check_button=PORT_CHECK, skip_first_screenshot=True)
