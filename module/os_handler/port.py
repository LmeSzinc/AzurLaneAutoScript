from module.base.timer import Timer
from module.logger import logger
from module.os_handler.assets import *
from module.os_handler.shop import OSShopHandler

# Azur Lane ports have PORT_GOTO_MISSION, PORT_GOTO_SUPPLY, PORT_GOTO_DOCK.
# Red axis ports have PORT_GOTO_SUPPLY.
# Use PORT_GOTO_SUPPLY as checker.
PORT_CHECK = PORT_GOTO_SUPPLY


class PortHandler(OSShopHandler):
    def port_enter(self, skip_first_screenshot=True):
        """
        Pages:
            in: IN_MAP
            out: PORT_CHECK
        """
        self.ui_click(PORT_ENTER, check_button=PORT_CHECK, skip_first_screenshot=skip_first_screenshot)
        # Buttons at the bottom has an animation to show
        pass  # Already ensured in ui_click

    def port_quit(self, skip_first_screenshot=True):
        """
        Pages:
            in: PORT_CHECK
            out: IN_MAP
        """
        self.ui_back(appear_button=PORT_CHECK, check_button=self.is_in_map,
                     skip_first_screenshot=skip_first_screenshot)
        # Buttons at the bottom has an animation to show
        self.wait_os_map_buttons()

    def port_mission_accept(self):
        """
        Accept all missions in port.

        Deprecated since 2022.01.13, missions are shown only in overview, no longer to be shown at ports.

        Returns:
            bool: True if all missions accepted or no mission found.
                  False if unable to accept more missions.

        Pages:
            in: PORT_CHECK
            out: PORT_CHECK
        """
        if not self.appear(PORT_MISSION_RED_DOT):
            logger.info('No available missions in this port')
            return True

        self.ui_click(PORT_GOTO_MISSION, appear_button=PORT_CHECK, check_button=PORT_MISSION_CHECK,
                      skip_first_screenshot=True)

        confirm_timer = Timer(1.5, count=3).start()
        skip_first_screenshot = True
        success = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(PORT_MISSION_ACCEPT, offset=(20, 20), interval=0.2):
                confirm_timer.reset()
                continue
            else:
                # End
                if confirm_timer.reached():
                    success = True
                    break

            if self.info_bar_count():
                logger.info('Unable to accept missions, because reached the maximum number of missions')
                success = False
                break

        self.ui_back(appear_button=PORT_MISSION_CHECK, check_button=PORT_CHECK, skip_first_screenshot=True)
        return success

    def port_supply_buy(self):
        """
        Buy supply in port.

        Returns:
            bool: True if success to buy any or no items found.
                False if not enough coins to buy any.

        Pages:
            in: PORT_CHECK
            out: PORT_CHECK
        """
        self.ui_click(PORT_GOTO_SUPPLY, appear_button=PORT_CHECK, check_button=PORT_SUPPLY_CHECK,
                      skip_first_screenshot=True)
        # Port items has an animation to show
        self.device.sleep(0.5)
        self.device.screenshot()

        success = self.handle_port_supply_buy()

        self.ui_back(appear_button=PORT_SUPPLY_CHECK, check_button=PORT_CHECK, skip_first_screenshot=True)
        return success

    def port_dock_repair(self):
        """
        Repair all ships.

        Pages:
            in: PORT_CHECK
            out: PORT_CHECK
        """
        self.ui_click(PORT_GOTO_DOCK, appear_button=PORT_CHECK, check_button=PORT_DOCK_CHECK,
                      skip_first_screenshot=True)

        skip_first_screenshot = True
        repaired = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.info_bar_count():
                break
            if repaired and self.appear(PORT_DOCK_CHECK, offset=(20, 20)):
                break

            # PORT_DOCK_CHECK is button to repair all.
            if self.appear_then_click(PORT_DOCK_CHECK, offset=(20, 20), interval=2):
                continue
            if self.handle_popup_confirm('DOCK_REPAIR'):
                repaired = True
                continue

        self.ui_back(appear_button=PORT_DOCK_CHECK, check_button=PORT_CHECK, skip_first_screenshot=True)
