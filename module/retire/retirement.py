from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.base.utils import color_similar, get_color, resize
from module.combat.assets import GET_ITEMS_1
from module.exception import RequestHumanTakeover, ScriptError
from module.handler.assets import AUTO_SEARCH_MAP_OPTION_OFF, AUTO_SEARCH_MAP_OPTION_ON
from module.logger import logger
from module.retire.assets import *
from module.retire.enhancement import Enhancement
from module.retire.scanner import ShipScanner
from module.retire.setting import QuickRetireSettingHandler
from module.ui.scroll import Scroll

CARD_GRIDS = ButtonGrid(
    origin=(93, 76), delta=(164 + 2 / 3, 227), button_shape=(138, 204), grid_shape=(7, 2), name='CARD')
CARD_RARITY_GRIDS = ButtonGrid(
    origin=(93, 76), delta=(164 + 2 / 3, 227), button_shape=(138, 5), grid_shape=(7, 2), name='RARITY')

CARD_RARITY_COLORS = {
    'N': (174, 176, 187),
    'R': (106, 195, 248),
    'SR': (151, 134, 254),
    'SSR': (248, 223, 107)
    # Not support marriage cards.
}

RETIRE_CONFIRM_SCROLL = Scroll(RETIRE_CONFIRM_SCROLL_AREA, color=(74, 77, 110), name='STRATEGIC_SEARCH_SCROLL')
RETIRE_CONFIRM_SCROLL.color_threshold = 240  # Background color is (66, 72, 77), so default (256-221)=35 is not enough to dintinguish.


class Retirement(Enhancement, QuickRetireSettingHandler):
    _unable_to_enhance = False
    _have_kept_cv = True

    # From MapOperation
    map_cat_attack_timer = Timer(2)

    @property
    def retire_keep_common_cv(self):
        return self.config.is_task_enabled('GemsFarming')

    def _retirement_choose(self, amount=10, target_rarity=('N',)):
        """
        Args:
            amount (int): Amount of cards retire. 0 to 10.
            target_rarity (tuple(str)): Card rarity. N, R, SR, SSR.

        Returns:
            int: Amount of cards have retired.
        """
        cards = []
        rarity = []
        for x, y, button in CARD_RARITY_GRIDS.generate():
            card_color = get_color(image=self.device.image, area=button.area)
            f = False
            for r, rarity_color in CARD_RARITY_COLORS.items():

                if color_similar(card_color, rarity_color, threshold=15):
                    cards.append([x, y])
                    rarity.append(r)
                    f = True

            if not f:
                logger.warning(
                    f'Unknown rarity color. Grid: ({x}, {y}). Color: {card_color}')

        logger.info(' '.join([r.rjust(3) for r in rarity[:7]]))
        logger.info(' '.join([r.rjust(3) for r in rarity[7:]]))

        selected = 0
        for card, r in zip(cards, rarity):
            if r in target_rarity:
                self.device.click(CARD_GRIDS[card])
                self.device.sleep((0.1, 0.15))
                selected += 1
            if selected >= amount:
                break
        return selected

    def _retirement_confirm(self, skip_first_screenshot=True):
        """
        Pages:
            in: IN_RETIREMENT_CHECK, and also
                SHIP_CONFIRM_2 if using one_click_retire
                SHIP_CONFIRM if using old_retire
            out: IN_RETIREMENT_CHECK
        """
        logger.info('Retirement confirm')
        executed = False
        for button in [SHIP_CONFIRM, SHIP_CONFIRM_2, EQUIP_CONFIRM, EQUIP_CONFIRM_2, GET_ITEMS_1, SR_SSR_CONFIRM]:
            self.interval_clear(button)
        self.popup_interval_clear()
        timeout = Timer(10, count=10).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if timeout.reached():
                # Ships being used by GemsFarming have no equipment to disassemble
                # So `executed` is never set to True, causing infinite loop
                # Handled with dirty timeout, a better fix is required
                logger.warning('Wait _retirement_confirm timeout, assume finished')
                break
            # sometimes you have EQUIP_CONFIRM without black-blurred background
            # EQUIP_CONFIRM and IN_RETIREMENT_CHECK appears
            if self.appear(IN_RETIREMENT_CHECK, offset=(20, 20)) and not self.appear(EQUIP_CONFIRM, offset=(30, 30)):
                if executed:
                    break
            else:
                timeout.reset()

            # Click
            # Ship confirm, order by display hierarchy
            if self._unable_to_enhance \
                    or self.config.OldRetire_SR \
                    or self.config.OldRetire_SSR \
                    or self.config.Retirement_RetireMode == 'one_click_retire':
                if self.handle_popup_confirm(name='RETIRE_SR_SSR', offset=(20, 50)):
                    self.interval_reset([SHIP_CONFIRM, SHIP_CONFIRM_2])
                    continue
                if self.config.SERVER in ['cn', 'jp', 'tw'] and \
                        self.appear_then_click(SR_SSR_CONFIRM, offset=(20, 50), interval=2):
                    self.interval_reset([SHIP_CONFIRM, SHIP_CONFIRM_2])
                    continue
            if self.match_template_color(SHIP_CONFIRM_2, offset=(30, 30), interval=2):
                if self.retire_keep_common_cv and not self._have_kept_cv:
                    self.keep_one_common_cv()
                self.device.click(SHIP_CONFIRM_2)
                # GET_ITEMS_1 is going to appear, avoid re-entering ship confirm
                self.interval_clear(GET_ITEMS_1)
                self.interval_reset([SHIP_CONFIRM, SHIP_CONFIRM_2])
                continue
            if self.match_template_color(SHIP_CONFIRM, offset=(30, 30), interval=2):
                self.device.click(SHIP_CONFIRM)
                continue
            # Equip confirm
            if self.appear_then_click(EQUIP_CONFIRM, offset=(30, 30), interval=2):
                executed = True
                continue
            if self.appear_then_click(EQUIP_CONFIRM_2, offset=(30, 30), interval=2):
                self.interval_clear(GET_ITEMS_1)
                continue
            # Get items
            if self.appear(GET_ITEMS_1, offset=(30, 30), interval=2):
                self.device.click(GET_ITEMS_1_RETIREMENT_SAVE)
                self.interval_reset(SHIP_CONFIRM)
                continue

    def retirement_appear(self):
        return self.appear(RETIRE_APPEAR_1, offset=30) \
               and self.appear(RETIRE_APPEAR_2, offset=30) \
               and self.appear(RETIRE_APPEAR_3, offset=30)

    def _retirement_quit(self):
        def check_func():
            return not self.appear(IN_RETIREMENT_CHECK, offset=(20, 20)) \
                   and not self.appear(DOCK_CHECK, offset=(20, 20))

        self.ui_back(check_button=check_func, skip_first_screenshot=True)

    @property
    def _retire_rarity(self):
        rarity = set()
        if self.config.OldRetire_N:
            rarity.add('N')
        if self.config.OldRetire_R:
            rarity.add('R')
        if self.config.OldRetire_SR:
            rarity.add('SR')
        if self.config.OldRetire_SSR:
            rarity.add('SSR')
        return rarity

    def _retire_wait_slow_retire(self, skip_first_screenshot=True):
        """
        SHIP_CONFIRM_2 may slow to appear on slow devices or large dock, wait it
        If SHIP_CONFIRM_2 can't be waited within 60s, GameStuckError will be raised

        Returns:
            bool: If SHIP_CONFIRM_2 appears
        """
        logger.info('Wait slow retire')
        self.device.click_record_clear()
        self.device.stuck_record_clear()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(SHIP_CONFIRM_2, offset=(30, 30)):
                return True

    def retire_ships_one_click(self):
        logger.hr('Retirement')
        logger.info('Using one click retirement.')
        # No need to wait, one-click-retire doesn't need to check dock
        self.dock_favourite_set(wait_loading=False)
        self.dock_sort_method_dsc_set(wait_loading=False)
        end = False
        total = 0

        if self.retire_keep_common_cv:
            self._have_kept_cv = False

        while 1:
            self.handle_info_bar()

            # ONE_CLICK_RETIREMENT -> SHIP_CONFIRM_2 or info_bar_count
            skip_first_screenshot = True
            click_count = 0
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()
                # End
                if self.appear(SHIP_CONFIRM_2, offset=(30, 30)):
                    break
                if self.info_bar_count():
                    logger.info('No more ships to retire.')
                    end = True
                    break

                # Click
                if click_count >= 5:
                    logger.warning('Failed to select ships using ONE_CLICK_RETIREMENT after 5 trial')
                    if self._retire_wait_slow_retire():
                        # Waited, all good
                        # Use pass to trigger ONE_CLICK_RETIREMENT on the same screenshot
                        pass
                    else:
                        # probably because game bugged, a re-enter should fix it
                        # Mark as retire finished, higher level will call retires
                        end = True
                        total = 10
                        break
                if self.appear_then_click(ONE_CLICK_RETIREMENT, offset=(20, 20), interval=2):
                    click_count += 1
                    continue

            # info_bar_count
            if end:
                break
            # SHIP_CONFIRM_2 -> IN_RETIREMENT_CHECK
            self._retirement_confirm()
            total += 10
            # if total >= amount:
            #     break
            # Always break, since game client retire all once
            break

        logger.info(f'Total retired round: {total // 10}')
        return total

    def retire_ships_old(self, amount=None, rarity=None):
        """
        Args:
            amount (int): Amount of cards retire. 0 to 2000.
            rarity (tuple(str)): Card rarity. N, R, SR, SSR.

        Returns:
            int: Total retired.
        """
        if amount is None:
            amount = self._retire_amount
        if rarity is None:
            rarity = self._retire_rarity
        logger.hr('Retirement')
        logger.info(f'Amount={amount}. Rarity={rarity}')

        # transfer N R SR SSR to filter name
        correspond_name = {
            'N': 'common',
            'R': 'rare',
            'SR': 'elite',
            'SSR': 'super_rare'
        }
        _rarity = [correspond_name[i] for i in rarity]
        self.dock_sort_method_dsc_set(False, wait_loading=False)
        self.dock_favourite_set(False, wait_loading=False)
        self.dock_filter_set(
            sort='level', index='all', faction='all', rarity=_rarity, extra='no_limit')

        total = 0

        if self.retire_keep_common_cv:
            self._have_kept_cv = False

        while amount:
            selected = self._retirement_choose(
                amount=10 if amount > 10 else amount, target_rarity=rarity)
            total += selected
            if selected == 0:
                break
            self.device.screenshot()
            if not self.match_template_color(SHIP_CONFIRM, offset=(30, 30)):
                logger.warning('No ship selected, retrying')
                continue

            self._retirement_confirm()

            amount -= selected
            if amount <= 0:
                break

            self.handle_dock_cards_loading()
            continue

        self.dock_sort_method_dsc_set(True, wait_loading=False)
        self.dock_filter_set()
        logger.info(f'Total retired: {total}')
        return total

    def retire_gems_farming_flagships(self, keep_one=True) -> int:
        """
        Retire abandoned flagships of GemsFarming.
        Common CV whose level > 1, fleet is none and status is free
        will be regarded as targets.
        """
        logger.info('Retire abandoned flagships of GemsFarming')

        gems_farming_enable: bool = self.config.is_task_enabled('GemsFarming')
        if not gems_farming_enable:
            logger.info('Not in GemsFarming, skip')
            return 0

        self.dock_favourite_set(wait_loading=False)
        self.dock_sort_method_dsc_set(wait_loading=False)
        self.dock_filter_set(index='cv', rarity='common', extra='not_level_max', sort='level')

        scanner = ShipScanner(
            rarity='common', fleet=0, status='free', level=(2, 100))
        scanner.disable('emotion')

        total = 0
        _ = self._have_kept_cv
        self._have_kept_cv = True

        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            self.handle_info_bar()
            ships = scanner.scan(self.device.image)
            if not ships:
                # exit if nothing can be retired
                break
            if keep_one:
                if len(ships) < 2:
                    break
                else:
                    # Try to keep the one with the lowest level
                    ships.sort(key=lambda s: -s.level)
                    ships = ships[:-1]

            for ship in ships:
                self.device.click(ship.button)
                self.device.sleep((0.1, 0.15))
                total += 1

            self._retirement_confirm()

            # Quick exit if there's only a few CV to retire
            if len(ships) < 10:
                break

        self._have_kept_cv = _
        # No need to wait, retire finished, just about to exit
        self.dock_filter_set(wait_loading=False)

        return total

    def handle_retirement(self):
        """
        Returns:
            bool: If retired.
        """
        if self._unable_to_enhance:
            if self.appear_then_click(RETIRE_APPEAR_1, offset=(20, 20), interval=3):
                self.interval_clear(IN_RETIREMENT_CHECK)
                self.interval_reset([AUTO_SEARCH_MAP_OPTION_OFF, AUTO_SEARCH_MAP_OPTION_ON])
                self.map_cat_attack_timer.reset()
                return False
            if self.appear(IN_RETIREMENT_CHECK, offset=(20, 20), interval=10):
                self._retire_handler(mode='one_click_retire')
                self._unable_to_enhance = False
                self.interval_reset(IN_RETIREMENT_CHECK)
                self.map_cat_attack_timer.reset()
                return True
        elif self.config.Retirement_RetireMode == 'enhance':
            if self.appear_then_click(RETIRE_APPEAR_3, offset=(20, 20), interval=3):
                self.interval_clear(DOCK_CHECK)
                self.interval_reset([AUTO_SEARCH_MAP_OPTION_OFF, AUTO_SEARCH_MAP_OPTION_ON])
                self.map_cat_attack_timer.reset()
                return False
            if self.appear(DOCK_CHECK, offset=(20, 20), interval=10):
                self.handle_dock_cards_loading()
                total, remain = self._enhance_handler()
                if not total:
                    logger.info(
                        'No ship to enhance, but dock full, will try retire')
                    self._unable_to_enhance = True
                logger.info(f'The remaining spare dock amount is {remain}')
                if remain < 3:
                    logger.info('Too few spare docks, retire next time')
                    self._unable_to_enhance = True
                self.interval_reset(DOCK_CHECK)
                self.map_cat_attack_timer.reset()
                return True
        else:
            if self.appear_then_click(RETIRE_APPEAR_1, offset=(20, 20), interval=3):
                self.interval_clear(IN_RETIREMENT_CHECK)
                self.interval_reset([AUTO_SEARCH_MAP_OPTION_OFF, AUTO_SEARCH_MAP_OPTION_ON])
                self.map_cat_attack_timer.reset()
                return False
            if self.appear(IN_RETIREMENT_CHECK, offset=(20, 20), interval=10):
                self._retire_handler()
                self._unable_to_enhance = False
                self.interval_reset(IN_RETIREMENT_CHECK)
                self.map_cat_attack_timer.reset()
                return True

        return False

    def _retire_handler(self, mode=None):
        """
        Args:
            mode (str): `one_click_retire` or `old_retire`

        Returns:
            int: Amount of retired ships

        Pages:
            in: IN_RETIREMENT_CHECK
            out: the page before retirement popup
        """
        if mode is None:
            mode = self.config.Retirement_RetireMode

        if mode == 'one_click_retire':
            total = self.retire_ships_one_click()
            if not total:
                logger.warning(
                    'No ship retired, trying to reset dock filter and disable favourite, then retire again')
                self.dock_favourite_set(False, wait_loading=False)
                self.dock_filter_set()
                total = self.retire_ships_one_click()
            if self.server_support_quick_retire_setting_fallback():
                # Some users may have already set filter_5='all', try with it first
                if not total:
                    logger.warning('No ship retired, trying to reset the first 4 quick retire settings')
                    self.quick_retire_setting_set(filter_5=None)
                    total = self.retire_ships_one_click()
                if not total:
                    logger.warning('No ship retired, trying to reset quick retire settings to "keep_limit_break"')
                    self.quick_retire_setting_set(filter_5='keep_limit_break')
                    total = self.retire_ships_one_click()
                if not total and self.config.OneClickRetire_KeepLimitBreak == 'do_not_keep':
                    logger.warning('No ship retired, trying to reset quick retire settings to "all"')
                    self.quick_retire_setting_set('all')
                    total = self.retire_ships_one_click()
            total += self.retire_gems_farming_flagships(keep_one=total > 0)
            if not total:
                logger.critical('No ship retired')
                logger.critical('Please configure your "Quick Retire Options" in game, '
                                'make sure it can select ships to retire')
                raise RequestHumanTakeover
        elif mode == 'old_retire':
            self.handle_dock_cards_loading()
            total = self.retire_ships_old()
            total += self.retire_gems_farming_flagships()
            if not total:
                logger.critical('No ship retired')
                logger.critical('Please configure your retirement settings in Alas, '
                                'make sure it can select ships to retire')
                raise RequestHumanTakeover
        else:
            raise ScriptError(
                f'Unknown retire mode: {self.config.Retirement_RetireMode}')

        self._retirement_quit()
        self.config.DOCK_FULL_TRIGGERED = True

        return total

    def _retire_select_one(self, button, skip_first_screenshot=True):
        """
        Args:
            button (Button): Ship button to select
            skip_first_screenshot:
        """
        count = 0
        RETIRE_COIN.load_color(self.device.image)
        RETIRE_COIN._match_init = True
        self.interval_clear(SHIP_CONFIRM_2)

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if not RETIRE_COIN.match(self.device.image, offset=(20, 20), similarity=0.97):
                return True
            if count > 3:
                logger.warning('_retire_select_one failed after 3 trial')
                return False

            if self.appear(SHIP_CONFIRM_2, offset=(30, 30), interval=2):
                self.device.click(button)
                count += 1
                continue

    def retirement_get_common_rarity_cv_in_page(self):
        """
        Returns:
            Button:
        """
        if self.config.GemsFarming_CommonCV == 'any':
            for common_cv_name in ['BOGUE', 'HERMES', 'LANGLEY', 'RANGER']:
                template = globals()[f'TEMPLATE_{common_cv_name}']
                sim, button = template.match_result(
                    resize(self.device.image, size=(1189, 669)))

                if sim > self.config.COMMON_CV_THRESHOLD:
                    return Button(button=tuple(_ * 155 // 144 for _ in button.button), area=button.area,
                                  color=button.color,
                                  name=f'TEMPLATE_{common_cv_name}_RETIRE')

            return None
        else:

            template = globals()[
                f'TEMPLATE_{self.config.GemsFarming_CommonCV.upper()}']
            sim, button = template.match_result(
                resize(self.device.image, size=(1189, 669)))

            if sim > self.config.COMMON_CV_THRESHOLD:
                return Button(button=tuple(_ * 155 // 144 for _ in button.button), area=button.area, color=button.color,
                              name=f'TEMPLATE_{self.config.GemsFarming_CommonCV.upper()}_RETIRE')

            return None

    def retirement_get_common_rarity_cv(self, skip_first_screenshot=False):
        """
        Args:
            skip_first_screenshot:

        Returns:
            Button: Button to click to remove ship from retire list
        """
        swipe_count = 0
        disappear_confirm = Timer(2, count=6)
        top_checked = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Try to get CV
            button = self.retirement_get_common_rarity_cv_in_page()
            if button is not None:
                return button

            # Wait scroll bar
            if RETIRE_CONFIRM_SCROLL.appear(main=self):
                disappear_confirm.clear()
            else:
                disappear_confirm.start()
                if disappear_confirm.reached():
                    logger.warning('Scroll bar disappeared, stop')
                    break
                else:
                    continue

            if not top_checked:
                top_checked = True
                logger.info('Find common CV from bottom to top')
                RETIRE_CONFIRM_SCROLL.set_bottom(main=self)
                continue
            else:
                if RETIRE_CONFIRM_SCROLL.at_top(main=self):
                    logger.info('Scroll bar reached top, stop')
                    break
                # Swipe prev page
                if swipe_count >= 7:
                    logger.info('Reached maximum swipes to find common CV')
                    break
                RETIRE_CONFIRM_SCROLL.prev_page(main=self)
                swipe_count += 1

        return button

    def keep_one_common_cv(self):
        """
        Returns:

        """
        logger.info('Keep one common CV')
        button = self.retirement_get_common_rarity_cv()
        if button is not None:
            self._retire_select_one(button)
            self._have_kept_cv = True
        logger.info('Keep one common CV end')
