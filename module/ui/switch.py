from module.base.base import ModuleBase
from module.base.button import Button
from module.base.timer import Timer
from module.exception import ScriptError
from module.logger import logger


class Switch:
    """
    A wrapper to handle switches in game, switch among states with reties.

    Examples:
        # Definitions
        submarine_hunt = Switch('Submarine_hunt', offset=120)
        submarine_hunt.add_state('on', check_button=SUBMARINE_HUNT_ON)
        submarine_hunt.add_state('off', check_button=SUBMARINE_HUNT_OFF)

        # Change state to ON
        submarine_view.set('on', main=self)
    """

    def __init__(self, name='Switch', is_selector=False):
        """
        Args:
            name (str):
            is_selector (bool): True if this is a multi choice, click to choose one of the switches.
                For example: | [Daily] | Urgent | -> click -> | Daily | [Urgent] |
                False if this is a switch, click the switch itself, and it changed in the same position.
                For example: | [ON] | -> click -> | [OFF] |
        """
        self.name = name
        self.is_choice = is_selector
        self.state_list = []

    def add_state(self, state, check_button, click_button=None):
        """
        Args:
            state (str):
            check_button (Button):
            click_button (Button):
        """
        self.state_list.append({
            'state': state,
            'check_button': check_button,
            'click_button': click_button if click_button is not None else check_button,
        })

    def appear(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            bool
        """
        for data in self.state_list:
            if main.appear(data['check_button']):
                return True

        return False

    def get(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            str: state name or 'unknown'.
        """
        for data in self.state_list:
            if main.appear(data['check_button']):
                return data['state']

        return 'unknown'

    def click(self, state, main):
        """
        Args:
            state (str):
            main (ModuleBase):
        """
        button = self.get_data(state)['click_button']
        main.device.click(button)

    def get_data(self, state):
        """
        Args:
            state (str):

        Returns:
            dict: Dictionary in add_state

        Raises:
            ScriptError: If state invalid
        """
        for row in self.state_list:
            if row['state'] == state:
                return row

        logger.warning(f'Switch {self.name} received an invalid state {state}')
        raise ScriptError(f'Switch {self.name} received an invalid state {state}')

    def handle_additional(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            bool: If handled
        """
        return False

    def set(self, state, main, skip_first_screenshot=True):
        """
        Args:
            state:
            main (ModuleBase):
            skip_first_screenshot (bool):

        Returns:
            bool: If clicked
        """
        logger.info(f'{self.name} set to {state}')
        self.get_data(state)

        counter = 0
        changed = False
        warning_show_timer = Timer(5, count=10).start()
        click_timer = Timer(1, count=3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            # Detect
            current = self.get(main=main)
            logger.attr(self.name, current)

            # Handle additional popups
            if self.handle_additional(main=main):
                continue

            # End
            if current == state:
                return changed

            # Warning
            if current == 'unknown':
                if warning_show_timer.reached():
                    logger.warning(f'Unknown {self.name} switch')
                    warning_show_timer.reset()
                    if counter >= 1:
                        logger.warning(f'{self.name} switch {state} asset has evaluated to unknown too many times, '
                                       f'asset should be re-verified')
                        return False
                    counter += 1
                continue

            # Click
            if click_timer.reached():
                click_state = state if self.is_choice else current
                self.click(click_state, main=main)
                click_timer.reset()
                changed = True

        return changed
