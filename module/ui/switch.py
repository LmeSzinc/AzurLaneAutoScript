from module.base.base import ModuleBase
from module.base.button import Button
from module.base.timer import Timer
from module.exception import ScriptError
from module.logger import logger


class Switch:
    """
    A wrapper to handle switches in game.
    Set switch status with reties.

    Examples:
        # Definitions
        submarine_hunt = Switch('Submarine_hunt', offset=120)
        submarine_hunt.add_status('on', check_button=SUBMARINE_HUNT_ON)
        submarine_hunt.add_status('off', check_button=SUBMARINE_HUNT_OFF)

        # Change status to ON
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
            offset (bool, int, tuple): Global offset in current switch
        """
        self.name = name
        self.is_choice = is_selector
        self.offset = offset
        self.status_list = []

    def add_status(self, status, check_button, click_button=None, offset=0):
        """
        Args:
            status (str):
            check_button (Button):
            click_button (Button):
            offset (bool, int, tuple):
        """
        self.status_list.append({
            'status': status,
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
        for data in self.status_list:
            if main.appear(data['check_button'], offset=data['offset']):
                return True

        return False

    def get(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            str: Status name or 'unknown'.
        """
        for data in self.status_list:
            if main.appear(data['check_button'], offset=data['offset']):
                return data['status']

        return 'unknown'

    def get_data(self, status):
        """
        Args:
            status (str):

        Returns:
            dict: Dictionary in add_status

        Raises:
            ScriptError: If status invalid
        """
        for row in self.status_list:
            if row['status'] == status:
                return row

        logger.warning(f'Switch {self.name} received an invalid status {status}')
        raise ScriptError(f'Switch {self.name} received an invalid status {status}')

    def handle_additional(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            bool: If handled
        """
        return False

    def set(self, status, main, skip_first_screenshot=True):
        """
        Args:
            status (str):
            main (ModuleBase):
            skip_first_screenshot (bool):

        Returns:
            bool:
        """
        self.get_data(status)

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
            if current == status:
                return changed

            # Warning
            if current == 'unknown':
                if warning_show_timer.reached():
                    logger.warning(f'Unknown {self.name} switch')
                    warning_show_timer.reset()
                    if counter >= 1:
                        logger.warning(f'{self.name} switch {status} asset has evaluated to unknown too many times, '
                                       f'asset should be re-verified')
                        return False
                    counter += 1
                continue

            # Click
            if click_timer.reached():
                click_status = status if self.is_choice else current
                main.device.click(self.get_data(click_status)['click_button'])
                click_timer.reset()
                changed = True

        return changed
