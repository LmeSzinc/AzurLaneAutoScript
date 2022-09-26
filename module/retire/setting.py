from module.base.decorator import cached_property
from module.retire.assets import *
from module.ui.setting import Setting
from module.ui.ui import UI


class QuickRetireSetting(Setting):
    def is_option_active(self, option: Button) -> bool:
        return self.main.image_color_count(option, color=(255, 255, 255), threshold=221, count=50)


class QuickRetireSettingHandler(UI):
    def _retire_setting_enter(self):
        """
        Pages:
            in: IN_RETIREMENT_CHECK, RETIRE_SETTING_ENTER
            out: RETIRE_SETTING_QUIT
        """
        self.ui_click(RETIRE_SETTING_ENTER, check_button=RETIRE_SETTING_QUIT,
                      offset=(30, 100), retry_wait=3, skip_first_screenshot=True)

    def _retire_setting_quit(self):
        """
        Pages:
            in: RETIRE_SETTING_QUIT
            out: IN_RETIREMENT_CHECK, RETIRE_SETTING_ENTER
        """
        self.ui_click(RETIRE_SETTING_QUIT, check_button=RETIRE_SETTING_ENTER,
                      offset=(30, 100), retry_wait=3, skip_first_screenshot=True)

    @cached_property
    def retire_setting(self) -> QuickRetireSetting:
        setting = QuickRetireSetting(name='RETIRE', main=self)
        setting.reset_first = False
        setting.add_setting(
            setting='filter_1',
            option_buttons=[RETIRE_SETTING_1],
            option_names=['R'],
            option_default='R'
        )
        setting.add_setting(
            setting='filter_2',
            option_buttons=[RETIRE_SETTING_2],
            option_names=['E'],
            option_default='E'
        )
        setting.add_setting(
            setting='filter_3',
            option_buttons=[RETIRE_SETTING_3],
            option_names=['N'],
            option_default='N'
        )
        setting.add_setting(
            setting='filter_4',
            option_buttons=[RETIRE_SETTING_4],
            option_names=['all'],
            option_default='all'
        )
        setting.add_setting(
            setting='filter_5',
            option_buttons=[RETIRE_SETTING_5_PRESERVE, RETIRE_SETTING_5_ALL],
            option_names=['keep_limit_break', 'all'],
            option_default='all'
        )
        return setting

    def quick_retire_setting_set(self, filter_5='all'):
        """
        Set options of quick retire options.
        The first 4 options are forced to set to:
        - Prioritize Rarity 1: R (Rare)
        - Prioritize Rarity 1: E (Elite)
        - Prioritize Rarity 1: N (Normal)
        - If you own a ship that has been fully Limit Broken, this option
          determines what you want to do with the corresponding duplicate ships.
              Don't Keep

        Args:
            filter_5 (str, None): The fifth option in quick retire options.
                "If you own multiple copies of a ship that has not been fully Limit
                Broken, this option determines what you want to do with those copies."
                'keep_limit_break' for "Keep Enough to Max LB",
                'all' for "Don't Keep"
                None for don't change

        Pages:
            in: IN_RETIREMENT_CHECK, RETIRE_SETTING_ENTER
            out: IN_RETIREMENT_CHECK, RETIRE_SETTING_ENTER
        """
        self._retire_setting_enter()
        self.retire_setting.set(filter_5=filter_5)
        self._retire_setting_quit()

    def server_support_quick_retire_setting_fallback(self):
        """
        Fallback to the correct quick retire settings if user has wrong set.
        """
        return self.config.SERVER in ['cn']
