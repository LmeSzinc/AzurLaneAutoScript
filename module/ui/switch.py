from module.base.base import ModuleBase
from module.base.button import Button
from module.base.timer import Timer
from module.logger import logger


class Switch:
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

    def add_status(self, status, check_button, click_button=None, offset=0, sleep=(1.0, 1.2)):
        """
        Args:
            status (str):
            check_button (Button):
            click_button (Button):
            offset (bool, int, tuple):
            sleep (int, float, tuple):
        """
        self.status_list.append({
            'status': status,
            'check_button': check_button,
            'click_button': click_button if click_button is not None else check_button,
            'offset': offset if offset else self.offset,
            'sleep': sleep
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

    def set(self, status, main, skip_first_screenshot=True):
        """
        Args:
            status (str):
            main (ModuleBase):
            skip_first_screenshot (bool):

        Returns:
            bool:
        """
        counter = 0
        changed = False
        warning_show_timer = Timer(5, count=10).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            current = self.get(main=main)
            logger.attr(self.name, current)
            if current == status:
                return changed

            if current == 'unknown':
                if warning_show_timer.reached():
                    logger.warning(f'Unknown {self.name} switch')
                    warning_show_timer.reset()
                    if counter >= 1:
                        logger.warning(f'{self.name} switch {status} asset has evaluated to unknown too many times, asset should be re-verified')
                        return False
                    counter += 1
                continue

            click_status = status if self.is_choice else current
            for data in self.status_list:
                if data['status'] == click_status:
                    main.device.click(data['click_button'])
                    main.device.sleep(data['sleep'])
                    changed = True
