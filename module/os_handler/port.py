from module.base.timer import Timer
from module.logger import logger
from module.os_handler.assets import *
from module.ui.ui import UI

# Azur Lane ports have PORT_GOTO_MISSION, PORT_GOTO_SUPPLY, PORT_GOTO_DOCK.
# Red axis ports have PORT_GOTO_SUPPLY.
# Use PORT_GOTO_SUPPLY as checker.
PORT_CHECK = PORT_GOTO_SUPPLY


class PortHandler(UI):
    def port_enter(self, skip_first_screenshot=True):
        """
        Pages:
            in: IN_MAP
            out: PORT_CHECK
        """
        self.ui_click(PORT_ENTER, check_button=PORT_CHECK, skip_first_screenshot=skip_first_screenshot)

    def port_quit(self, skip_first_screenshot=True):
        """
        Pages:
            in: PORT_CHECK
            out: IN_MAP
        """
        self.ui_back(appear_button=PORT_CHECK, check_button=PORT_ENTER,
                     skip_first_screenshot=skip_first_screenshot)

    def port_mission_accept(self):
        """
        Accept all missions in port.

        Pages:
            in: PORT_CHECK
            out: PORT_CHECK
        """
        self.ui_click(PORT_GOTO_MISSION, appear_button=PORT_CHECK, check_button=PORT_MISSION_CHECK,
                      skip_first_screenshot=True)

        if self.appear(PORT_MISSION_RED_DOT):
            confirm_timer = Timer(1.5, count=3)
            skip_first_screenshot = True
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                if self.appear_then_click(PORT_MISSION_ACCEPT, offset=(20, 20), interval=0.35):
                    confirm_timer.reset()
                    continue
                else:
                    # End
                    if confirm_timer.reached():
                        break
        else:
            logger.info('No available missions in this port')

        self.ui_back(appear_button=PORT_MISSION_CHECK, check_button=PORT_CHECK, skip_first_screenshot=True)

    def port_supply_buy(self):
        """
        Buy supply in port.

        Pages:
            in: PORT_CHECK
            out: PORT_CHECK
        """
        self.ui_click(PORT_GOTO_SUPPLY, appear_button=PORT_CHECK, check_button=PORT_SUPPLY_CHECK,
                      skip_first_screenshot=True)

        pass

        self.ui_back(appear_button=PORT_SUPPLY_CHECK, check_button=PORT_CHECK, skip_first_screenshot=True)

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
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # PORT_DOCK_CHECK is button to repair all.
            if self.appear_then_click(PORT_DOCK_CHECK, offset=(20, 20), interval=2):
                continue
            if self.handle_popup_confirm('DOCK_REPAIR'):
                continue

            # End
            if self.info_bar_count():
                break

        self.ui_back(appear_button=PORT_DOCK_CHECK, check_button=PORT_CHECK, skip_first_screenshot=True)
