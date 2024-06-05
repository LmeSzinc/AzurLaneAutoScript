import copy
import typing as t

from module.base.base import ModuleBase
from module.base.button import Button, ButtonGrid
from module.base.timer import Timer
from module.config.utils import dict_to_kv
from module.exception import ScriptError
from module.logger import logger


class Setting:
    def __init__(self, name='Setting', main: ModuleBase = None):
        self.name = name
        # Alas module object
        self.main: ModuleBase = main
        # Reset options before setting any options
        self.reset_first = True
        # (setting, opiton_name): option_button
        # {
        #     ('sort', 'rarity'): Button(),
        #     ('sort', 'level'): Button(),
        #     ('sort', 'total'): Button(),
        # }
        self.settings: t.Dict[(str, str), Button] = {}
        # setting: option_name
        # {
        #     'sort': 'rarity',
        #     'index': 'all',
        # }
        self.settings_default: t.Dict[str, str] = {}

    def add_setting(self, setting, option_buttons, option_names, option_default):
        """
        Args:
            setting (str):
                Name of the setting
            option_buttons (list[Button], ButtonGrid):
                List of buttons produced by ButtonGrid.buttons
            option_names (list[str]):
                Name of each options, `option_names` and `options` must has the same length.
            option_default (str):
                Name of the default option, must in `option_names`
        """
        if isinstance(option_buttons, ButtonGrid):
            option_buttons = option_buttons.buttons
        for option, option_name in zip(option_buttons, option_names):
            self.settings[(setting, option_name)] = option

        if option_default not in option_names:
            raise ScriptError(f'Define option_default="{option_default}", '
                              f'but default is not in option_names={option_names}')
        self.settings_default[setting] = option_default

    def is_option_active(self, option: Button) -> bool:
        return self.main.image_color_count(option, color=(181, 142, 90), threshold=235, count=250) \
               or self.main.image_color_count(option, color=(74, 117, 189), threshold=235, count=250)

    def _product_setting_status(self, **kwargs) -> t.Dict[Button, bool]:
        """
        Args:
            **kwargs: Key: setting, value: required option or a list of them
                `sort=['rarity', 'level'], ...` or `sort='rarity'`,
                or `sort=None` means don't change this setting

        Returns:
            dict: Key: option_button, value: whether should be active
        """
        # Add defaults
        required_options = copy.deepcopy(self.settings_default)
        required_options.update(kwargs)

        # option_button: Whether should be active
        # {BUTTON_1: True, BUTTON_2: False, ...}
        status: t.Dict[Button, bool] = {}
        for key, option_button in self.settings.items():
            setting, option_name = key
            required = required_options[setting]
            if required is not None:
                required = required if isinstance(required, list) else [required]
                status[option_button] = option_name in required

        return status

    def show_active_buttons(self):
        """
        Logs:
            [Setting] sort/rarity, sort/level
        """
        active = []
        for key, option_button in self.settings.items():
            setting, option_name = key
            if self.is_option_active(option_button):
                active.append(f'{setting}/{option_name}')

        logger.attr(self.name, ', '.join(active))

    def get_buttons_to_click(self, status: t.Dict[Button, bool]) -> t.List[Button]:
        """
        Args:
            status: Key: option_button, value: whether should be active

        Returns:
            Buttons to click
        """
        click = []
        for option_button, enable in status.items():
            active = self.is_option_active(option_button)
            if enable and not active:
                click.append(option_button)
        return click

    def _set_execute(self, **kwargs):
        """
        Args:
            **kwargs: Key: setting, value: required option or a list of them
                `sort=['rarity', 'level'], ...` or `sort='rarity'`,
                or `sort=None` means don't change this setting

        Returns:
            bool: If success the set
        """
        status = self._product_setting_status(**kwargs)

        logger.info(f'Setting {self.name} options, {dict_to_kv(kwargs)}')
        skip_first_screenshot = True
        retry = Timer(1, count=2)
        timeout = Timer(10, count=20).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.main.device.screenshot()

            if timeout.reached():
                logger.warning(f'Set {self.name} options timeout, assuming current options are correct.')
                return False

            self.show_active_buttons()
            clicks = self.get_buttons_to_click(status)
            if clicks:
                if retry.reached():
                    for button in clicks:
                        self.main.device.click(button)
                    retry.reset()
            else:
                return True

    def set(self, **kwargs):
        """
        Args:
            **kwargs: Key: setting, value: required option or a list of them
                `sort=['rarity', 'level'], ...` or `sort='rarity'`,
                or `sort=None` means don't change this setting

        Returns:
            bool: If success the set
        """
        if self.reset_first:
            self._set_execute()  # Reset options
        self._set_execute(**kwargs)
