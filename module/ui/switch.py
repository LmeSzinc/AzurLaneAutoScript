from module.base.base import ModuleBase
from module.base.timer import Timer
from module.exception import ScriptError
from module.logger import logger


class Switch:
    """
    A wrapper to handle switches in game, switch among states with retries.

    Examples:
        # Definitions
        submarine_hunt = Switch('Submarine_hunt', offset=120)
        submarine_hunt.add_state('on', check_button=SUBMARINE_HUNT_ON)
        submarine_hunt.add_state('off', check_button=SUBMARINE_HUNT_OFF)

        # Change state to ON
        submarine_view.set('on', main=self)
    """

    def __init__(self, name='Switch', is_selector=False, offset=0):
        """
        Args:
            name (str):
            is_selector (bool): True if this is a multi choice, click to choose one of the switches.
                For example: | [Daily] | Urgent | -> click -> | Daily | [Urgent] |
                False if this is a switch, click the switch itself, and it changed in the same position.
                For example: | [ON] | -> click -> | [OFF] |
        """
        self.name = name
        self.is_selector = is_selector
        self.offset = offset
        self.state_list = []

    def add_state(self, state, check_button, click_button=None, offset=0):
        """
        Args:
            state (str): State name but cannot use 'unknown' as state name
            check_button (Button):
            click_button (Button):
            offset (bool, int, tuple):
        """
        if state == 'unknown':
            raise ScriptError(f'Cannot use "unknown" as state name')
        self.state_list.append({
            'state': state,
            'check_button': check_button,
            'click_button': click_button if click_button is not None else check_button,
            'offset': offset if offset else self.offset
        })

    def appear(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            bool
        """
        for data in self.state_list:
            if main.appear(data['check_button'], offset=data['offset']):
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
            if main.appear(data['check_button'], offset=data['offset']):
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

        raise ScriptError(f'Switch {self.name} received an invalid state: {state}')

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

        changed = False
        has_unknown = False
        unknown_timer = Timer(5, count=10).start()
        click_timer = Timer(1, count=3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            # Detect
            current = self.get(main=main)
            logger.attr(self.name, current)

            # End
            if current == state:
                return changed

            # Handle additional popups
            if self.handle_additional(main=main):
                continue

            # Warning
            if current == 'unknown':
                if unknown_timer.reached():
                    logger.warning(f'Switch {self.name} has states evaluated to unknown, '
                                   f'asset should be re-verified')
                    has_unknown = True
                    unknown_timer.reset()
                # If unknown_timer never reached, don't click when having an unknown state,
                # the unknown state is probably the switching animation.
                # If unknown_timer reached once, click target state ignoring whether state is unknown or not,
                # the unknown state is probably a new state not yet added.
                # By ignoring new states, Switch.set() can still switch among known states.
                if not has_unknown:
                    continue
            else:
                # Known state, reset timer
                unknown_timer.reset()

            # Click
            if click_timer.reached():
                if self.is_selector:
                    # Click target state to switch
                    click_state = state
                else:
                    # If this is a selector, click on current state to switch to another
                    # But 'unknown' is not clickable, if it is, click target state instead
                    # assuming all selector states share the same position.
                    if current == 'unknown':
                        click_state = state
                    else:
                        click_state = current
                self.click(click_state, main=main)
                changed = True
                click_timer.reset()
                unknown_timer.reset()

        return changed

    def wait(self, main, skip_first_screenshot=True):
        """
        Wait until any state activated

        Args:
            main (ModuleBase):
            skip_first_screenshot:

        Returns:
            bool: If success
        """
        timeout = Timer(2, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            # Detect
            current = self.get(main=main)
            logger.attr(self.name, current)

            # End
            if current != 'unknown':
                return True
            if timeout.reached():
                logger.warning(f'{self.name} wait activated timeout')
                return False

            # Handle additional popups
            if self.handle_additional(main=main):
                continue
