from re import sub
import numpy as np

from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.base.utils import color_similarity_2d
from module.combat.assets import GET_ITEMS_1
from module.handler.assets import POPUP_CONFIRM
from module.logger import logger
from module.ocr.ocr import Digit, Ocr
from module.reward.assets import *
from module.ui.ui import UI, page_guild

GUILD_EXCHANGE_LIMIT = Digit(OCR_GUILD_EXCHANGE_LIMIT, threshold=64)
GUILD_EXCHANGE_INFO_1 = Ocr(OCR_GUILD_EXCHANGE_INFO_1, lang='cnocr', letter=(148, 249, 99), threshold=64,
                            alphabet='0123ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz- ')
GUILD_EXCHANGE_INFO_2 = Digit(OCR_GUILD_EXCHANGE_INFO_2, lang='cnocr', letter=(148, 249, 99), threshold=64)

GUILD_SIDEBAR = ButtonGrid(
    origin=(21, 118), delta=(0, 94.5), button_shape=(60, 75), grid_shape=(1, 5), name='GUILD_SIDEBAR')

EXCHANGE_PRIORITY_ORDER_AND_COST = {
't1': 20,
'cola': 20,
't2': 10,
'secret': 20,
'coin': 600,
'oil': 200,
'merit': 450,
't3': 5
}

class RewardGuild(UI):
    def _guild_sidebar_click(self, index):
        """
        Performs the calculations necessary
        to determine the index location on
        sidebar and then click at that location

        Args:
            index (int):
                5 for lobby.
                4 for members.
                3 for logistics.
                2 for tech.
                1 for operations.

        Returns:
            bool: if changed.
        """
        if index <= 0 or index > 5:
            logger.warning(f'Sidebar index cannot be clicked, {index}, limit to 1 through 5 only')
            return False

        current = 0
        total = 0

        for idx, button in enumerate(GUILD_SIDEBAR.buttons()):
            image = np.array(self.device.image.crop(button.area))
            if np.sum(image[:, :, 0] > 235) > 100:
                current = idx + 1
                total = idx + 1
                continue
            if np.sum(color_similarity_2d(image, color=(140, 162, 181)) > 221) > 100:
                total = idx + 1
            else:
                break
        if not current:
            logger.warning('No guild sidebar active.')
        if total == 3:
            current = 4 - current
        elif total == 4:
            current = 5 - current
        elif total == 5:
            current = 6 - current
        else:
            logger.warning('Guild sidebar total count error.')

        logger.attr('Guild_sidebar', f'{current}/{total}')
        if current == index:
            return False

        diff = total - index
        if diff >= 0:
            self.device.click(GUILD_SIDEBAR[0, diff])
        else:
            logger.warning(f'Target index {index} cannot be clicked')
        return True

    def _guild_exchange_select(self, choices, btn_guild_logistics_check):
        """
        Execute exchange action on choices
        The order of selection based on item weight
        If none are applicable, return False

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        logger.info(choices)
        for i in range(3):
            # Pick the choice with the least item_weight
            # if same item_weight, min proceeds to next
            # iterable, which is the exchange button index
            key = min(choices, key=choices.get)
            details = choices.get(key)
            if details[2] <= details[3]:
                self.ui_click(click_button=details[4], check_button=POPUP_CONFIRM,
                              appear_button=btn_guild_logistics_check, skip_first_screenshot=True)
                self.handle_guild_confirm('GUILD_EXCHANGE', btn_guild_logistics_check)
                #self.handle_guild_cancel('GUILD_EXCHANGE', btn_guild_logistics_check)
                return True
            else:
                # Remove this choice since inapplicable, then choose again
                choices.pop(key)
        return False

    def _guild_exchange_check(self, btn_guild_logistics_check):
        """
        Sift through all exchangable options
        Record details on each to determine
        selection order

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        # Holds the details of all 3 choice options
        choices = dict()

        # Check all 3 available selections
        # Use Ocr to determine type, cost, and inventory of that item
        for index in range(3):
            index += 1
            btn_key = f'GUILD_EXCHANGE_{index}'
            btn = globals()[btn_key]
            self.ui_click(click_button=btn, check_button=POPUP_CONFIRM,
                          appear_button=btn_guild_logistics_check, skip_first_screenshot=True)

            item_text = (GUILD_EXCHANGE_INFO_1.ocr(self.device.image)).lower()

            # Defaults if Ocr were to fail, set absurd values forcing to skip the item upon selection
            item_weight = len(EXCHANGE_PRIORITY_ORDER_AND_COST)
            item_cost = 999999999
            item_inventory = 0
            for i, (key, value) in enumerate(EXCHANGE_PRIORITY_ORDER_AND_COST.items()):
                if key in item_text:
                    item_weight = i
                    item_cost = value
            item_inventory = GUILD_EXCHANGE_INFO_2.ocr(self.device.image)
            choices[f'{index}'] = [item_weight, index, item_cost, item_inventory, btn]

            self.handle_guild_cancel(btn_key, btn_guild_logistics_check)

        return choices

    def guild_sidebar_ensure(self, index, skip_first_screenshot=True):
        """
        Performs action to ensure the specified
        index sidebar is transitioned into
        Maximum of 3 attempts

        Args:
            index (int):
                5 for lobby.
                4 for members.
                3 for logistics.
                2 for tech.
                1 for operations.

        Returns:
            bool: sidebar click ensured or not
        """
        if index <= 0 or index > 5:
            logger.warning(f'Sidebar index cannot be ensured, {index}, limit 1 through 5 only')
            return False

        counter = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._guild_sidebar_click(index):
                if counter >= 2:
                    logger.warning('Sidebar could not be ensured')
                    return False
                counter += 1
                self.device.sleep((0.3, 0.5))
                continue
            else:
                return True

    def guild_logistics_ensure(self, skip_first_screenshot=True):
        """
        Ensure logistics page check either
        AZUR or AXIS

        Method also used as a means to determine
        which affiliation the player is

        Pages:
            in: ANY
            out: ANY
        """
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(GUILD_LOGISTICS_CHECK_AZUR) or self.appear(GUILD_LOGISTICS_CHECK_AXIS):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

        if self.appear(GUILD_LOGISTICS_CHECK_AZUR):
            return True
        else:
            return False

    def handle_guild_confirm(self, confirm_text, appear_button, skip_first_screenshot=True):
        """
        Execute confirm screen transitions

        Pages:
            in: ANY
            out: ANY
        """
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_popup_confirm(confirm_text):
                confirm_timer.reset()
                continue

            if self.appear_then_click(GET_ITEMS_1, offset=(30, 30), interval=1):
                confirm_timer.reset()
                continue

            # End
            if self.appear(appear_button):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

    def handle_guild_cancel(self, cancel_text, appear_button, skip_first_screenshot=True):
        """
        Execute cancel screen transitions

        Pages:
            in: ANY
            out: ANY
        """
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_popup_cancel(cancel_text):
                confirm_timer.reset()
                continue

            # End
            if self.appear(appear_button):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

    def guild_exchange(self, limit, btn_guild_logistics_check):
        """
        Performs sift check and executes the applicable
        exchanges, number performed based on limit
        If unable to exchange at all, loop terminates
        prematurely

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        for num in range(limit):
            choices = self._guild_exchange_check(btn_guild_logistics_check)
            if not self._guild_exchange_select(choices, btn_guild_logistics_check):
                logger.warning('Failed to exchange with any of the 3 available options')
                break
            self.ensure_no_info_bar()

    def guild_logistics(self):
        """
        Execute all actions in logistics

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """

        # Transition to Logistics
        # Additional wait time needed
        # as ensure does not wait for
        # page to load
        if not self.guild_sidebar_ensure(3):
            logger.info('Ensurance has failed, please join a Guild first')
            return
        is_affiliation_azur = self.guild_logistics_ensure()

        # After ensurance, use boolean returned to determine buttons
        btn_guild_mission_rewards = GUILD_MISSION_REWARDS_AZUR if is_affiliation_azur else GUILD_MISSION_REWARDS_AXIS
        btn_guild_mission_accept = GUILD_MISSION_ACCEPT_AZUR if is_affiliation_azur else GUILD_MISSION_ACCEPT_AXIS
        btn_guild_supply_rewards = GUILD_SUPPLY_REWARDS_AZUR if is_affiliation_azur else GUILD_SUPPLY_REWARDS_AXIS
        btn_guild_logistics_check = GUILD_LOGISTICS_CHECK_AZUR if is_affiliation_azur else GUILD_LOGISTICS_CHECK_AXIS

        # Execute all logistics actions
        # 1) Collect Mission Rewards if available
        # 2) Accept Mission if available
        # 3) Collect Supply Rewards if available
        # 4) Contribute resources if able
        if self.appear_then_click(btn_guild_mission_rewards, offset=(20, 20)):
            self.handle_guild_confirm('GUILD_MISSION_REWARDS', btn_guild_logistics_check)
            self.ensure_no_info_bar()

        if self.appear_then_click(btn_guild_mission_accept, offset=(20, 20)):
            self.handle_guild_confirm('GUILD_MISSION_ACCEPT', btn_guild_logistics_check)
            self.ensure_no_info_bar()

        if self.appear_then_click(btn_guild_supply_rewards, offset=(20, 20)):
            self.handle_guild_confirm('GUILD_SUPPLY_REWARDS', btn_guild_logistics_check)
            self.ensure_no_info_bar()

        GUILD_EXCHANGE_LIMIT.letter = (173, 182, 206) if is_affiliation_azur else (214, 113, 115)
        limit = GUILD_EXCHANGE_LIMIT.ocr(self.device.image)
        if limit > 0:
            self.guild_exchange(limit, btn_guild_logistics_check)

    def guild_operations(self):
        pass

    def guild_run(self, logistics=True, operations=True):
        """
        Execute logistics and operations actions
        if enabled by arguments

        Pages:
            in: Any page
            out: page_main
        """
        if not logistics and not operations:
            return False

        self.ui_ensure(page_guild)

        if logistics:
            self.guild_logistics()

        if operations:
            self.guild_operations()

        self.ui_goto_main()
        return True

    def handle_guild(self):
        """
        Returns:
            bool: If executed
        """
        if not self.config.ENABLE_GUILD_LOGISTICS and not self.config.ENABLE_GUILD_OPERATIONS:
            return False

        # Print out last date checked
        self.config.record_executed_since(option=('RewardRecord', 'guild'), since=(0,))

        # TODO: Because notification can appear for either logistics or operations,
        # currently ignored as operations is not yet supported, guild will be checked
        # every reward loop
        #self.ui_goto_main()
        #if not self.appear(GUILD_RED_DOT, offset=(30, 30)):
        #    logger.info('Nothing in guild to check for, no notification detected')
        #    return False

        if not self.guild_run(logistics=self.config.ENABLE_GUILD_LOGISTICS, operations=self.config.ENABLE_GUILD_OPERATIONS):
            return False

        self.config.record_save(option=('RewardRecord', 'guild'))
        return True
