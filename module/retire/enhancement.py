from random import choice

import numpy as np
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.combat.assets import GET_ITEMS_1
from module.handler.assets import INFO_BAR_DETECT
from module.handler.info_handler import info_letter_preprocess
from module.logger import logger
from module.retire.assets import *
from module.retire.dock import Dock, CARD_GRIDS
from module.template.assets import TEMPLATE_ENHANCE_SUCCESS, TEMPLATE_ENHANCE_FAILED, TEMPLATE_ENHANCE_IN_BATTLE

VALID_SHIP_TYPES = ['dd', 'ss', 'cl', 'ca', 'bb', 'cv', 'repair', 'others']


class Enhancement(Dock):
    @property
    def _retire_amount(self):
        if self.config.RETIRE_AMOUNT == 'all':
            return 2000
        if self.config.RETIRE_AMOUNT == '10':
            return 10
        return 10

    @cached_property
    def _load_enhance_template(self):
        TEMPLATE_ENHANCE_SUCCESS.image = info_letter_preprocess(TEMPLATE_ENHANCE_SUCCESS.image)
        TEMPLATE_ENHANCE_FAILED.image = info_letter_preprocess(TEMPLATE_ENHANCE_FAILED.image)
        TEMPLATE_ENHANCE_IN_BATTLE.image = info_letter_preprocess(TEMPLATE_ENHANCE_IN_BATTLE.image)
        return True

    def _enhance_enter(self, favourite=False, ship_type=None):
        """
        Pages:
            in: page_dock
            out: page_ship_enhance

        Returns:
            bool: False with filter applied resulting
                  in empty dock.
                  Otherwise true with at least 1 card
                  available to be picked.
        """
        if favourite:
            self.dock_favourite_set(enable=True)

        # self.dock_filter_enter()
        # self.dock_filter_set(category='extra', filter_type='enhanceable', enable=True)
        # self.dock_filter_set(category='index', filter_type='all', enable=True)
        # self.dock_filter_set(category='sort', filter_type='level', enable=True)
        # self.dock_filter_set(category='faction', filter_type='all', enable=True)
        # self.dock_filter_set(category='rarity', filter_type='all', enable=True)
        # if ship_type is not None:
        #     ship_type = str(ship_type)
        #     self.dock_filter_set(category='index', filter_type=ship_type, enable=True)
        # self.dock_filter_confirm()
        if ship_type is not None:
            ship_type = str(ship_type)
            self.dock_filter_set_faster(extra='enhanceable', index=ship_type)
        else:
            self.dock_filter_set_faster(extra='enhanceable')

        if self.appear(DOCK_EMPTY, offset=(30, 30)):
            return False

        self.equip_enter(CARD_GRIDS[(0, 0)], check_button=SHIP_DETAIL_CHECK, long_click=False)
        return True

    def _enhance_quit(self):
        """
        Pages:
            in: page_ship_enhance
            out: page_dock
        """
        self.ui_back(DOCK_FILTER)
        self.dock_favourite_set(enable=False)
        # self.dock_filter_enter()
        # self.dock_filter_set(category='extra', filter_type='no_limit', enable=True)
        # self.dock_filter_set(category='index', filter_type='all', enable=True)
        # self.dock_filter_confirm()
        self.dock_filter_set_faster()

    def _enhance_confirm(self, skip_first_screenshot=True):
        """
        Pages:
            in: EQUIP_CONFIRM
            out: page_ship_enhance, without info_bar
        """

        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(EQUIP_CONFIRM, offset=(30, 30), interval=3):
                confirm_timer.reset()
                continue
            if self.appear_then_click(EQUIP_CONFIRM_2, offset=(30, 30), interval=3):
                confirm_timer.reset()
                continue
            if self.appear(GET_ITEMS_1, interval=2):
                self.device.click(GET_ITEMS_1_RETIREMENT_SAVE)
                self.interval_reset(ENHANCE_CONFIRM)
                confirm_timer.reset()
                continue

            # End
            if self.appear(ENHANCE_CONFIRM, offset=(30, 30)):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

    def _enhance_choose(self, ship_count):
        """
        Re-vamped implementation, utilizing
        templates and info_bar text to determine
        whether a ship can or cannot be enhanced
        Method similar to ambush.py

        Pages:
            in: page_ship_enhance, without info_bar
            out: EQUIP_CONFIRM

        Args:
            ship_count (int): ship_count, must be
            non-zero positive integer

        Returns:
            True if able to enhance otherwise False
            Always paired with current ship_count
        """
        _ = self._load_enhance_template
        skip_until_ensured = True
        enhanced = False
        while 1:
            # Base Case: No more ships left to check for this category
            if ship_count <= 0:
                logger.info('Reached maximum number to check, exiting current category')
                return False, ship_count

            if skip_until_ensured:
                if not self.equip_side_navbar_ensure(bottom=4):
                    continue
                self.wait_until_appear(ENHANCE_RECOMMEND, offset=(5, 5), skip_first_screenshot=True)
                skip_until_ensured = False
            else:
                self.device.screenshot()

            if self.handle_popup_confirm('ENHANCE'):
                continue

            # Respond accordingly based on info_bar information
            if self.info_bar_count():
                image = info_letter_preprocess(np.array(self.device.image.crop(INFO_BAR_DETECT.area)))
                if TEMPLATE_ENHANCE_SUCCESS.match(image):
                    enhanced = True
                elif TEMPLATE_ENHANCE_FAILED.match(image):
                    logger.info('Enhancement failed. Swiping to next ship if feasible')
                    self.ensure_no_info_bar()
                    if self.equip_view_next(check_button=ENHANCE_RECOMMEND):
                        ship_count -= 1
                        continue
                    else:
                        logger.info('Swiped failed, exiting current category')
                        return False, ship_count
                elif TEMPLATE_ENHANCE_IN_BATTLE.match(image):
                    logger.info('Enhancement impossible, ship currently in battle. Swiping to next ship if feasible')
                    self.ensure_no_info_bar()
                    if self.equip_view_next(check_button=ENHANCE_RECOMMEND):
                        continue
                    else:
                        logger.info('Swiped failed, exiting current category')
                        return False, ship_count

            # Possible trapped case in which info_bar will never appear
            # so long as EQUIP_CONFIRM remains appeared
            if enhanced or self.appear(EQUIP_CONFIRM, offset=(30, 30)):
                logger.info('Enhancement Successful')
                return True, ship_count

            # Perform actions to attempt enhancement
            if self.appear_then_click(ENHANCE_RECOMMEND, offset=(5, 5), interval=2):
                self.device.sleep(0.3)
                self.device.click(ENHANCE_CONFIRM)
                logger.info('Enhancing...')

    def enhance_ships(self, favourite=None):
        """
        Enhance target ships by specified order
        of types listed in ENHANCE_ORDER_STRING

        Invalid types are treated as requesting
        from ALAS to choose a valid one at random

        Pages:
            in: page_dock
            out: page_dock

        Args:
            favourite (bool):

        Returns:
            int: total enhanced
        """
        if favourite is None:
            favourite = self.config.ENHANCE_FAVOURITE

        logger.hr('Enhancement by type')
        total = 0

        # Process ENHANCE_ORDER_STRING if any into ship_types
        ship_types = [s.strip().lower() for s in self.config.ENHANCE_ORDER_STRING.split('>')]
        ship_types = list(filter(''.__ne__, ship_types))
        if len(ship_types) == 0:
            ship_types = [None]
        logger.attr('Enhance Order', ship_types)

        # Process available ship types for choice randomization
        # Removing types that have already been specified by
        # ENHANCE_ORDER_STRING
        available_ship_types = VALID_SHIP_TYPES.copy()
        [available_ship_types.remove(s) for s in ship_types if s in available_ship_types]

        for ship_type in ship_types:
            # None check, do not execute if is None
            # Otherwise, select a type at random since
            # user has specified an unrecognized type
            if ship_type is not None and ship_type not in VALID_SHIP_TYPES:
                if len(available_ship_types) == 0:
                    logger.info('No more ship types for ALAS to choose from, skipping iteration')
                    continue
                ship_type = choice(available_ship_types)
                available_ship_types.remove(ship_type)

            logger.info(f'Favourite={favourite}, Ship Type={ship_type}')

            # Continue if at least 1 CARD_GRID is selectable
            # otherwise skip to next ship type
            if not self._enhance_enter(favourite=favourite, ship_type=ship_type):
                logger.hr(f'Dock Empty by ship type {ship_type}')
                continue

            current_count = self.config.ENHANCE_CHECK_PER_CATEGORY
            while 1:
                choose_result, current_count = self._enhance_choose(ship_count=current_count)
                if not choose_result:
                    break
                self._enhance_confirm()
                total += 10
                if total >= self._retire_amount:
                    break
            self.ui_back(DOCK_FILTER)

        self._enhance_quit()
        return total

    def _enhance_handler(self):
        """
        Pages:
            in: RETIRE_APPEAR
            out:

        Returns:
            int: enhance turn count
        """
        self.ui_click(RETIRE_APPEAR_3, check_button=DOCK_FILTER, skip_first_screenshot=True)
        self.handle_dock_cards_loading()

        total = self.enhance_ships()

        self.dock_quit()
        self.config.DOCK_FULL_TRIGGERED = True

        return total
