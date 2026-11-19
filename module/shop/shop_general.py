from module.base.decorator import cached_property
from module.config.utils import random_id
from module.logger import logger
from module.shop.base import ShopItemGrid, ShopItemGrid_250814
from module.shop.clerk import ShopClerk
from module.shop.shop_status import ShopStatus
from module.shop.skin_box import parse_skin_box_slots, skin_box_counter
from module.shop.ui import ShopUI


class GeneralShop_250814(ShopClerk, ShopUI, ShopStatus):
    gems = 0
    shop_template_folder = './assets/shop/general'

    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        return self.config.GeneralShop_Filter.strip()

    # New UI in 2025-08-14
    @cached_property
    def shop_general_items(self):
        """
        Returns:
            ShopItemGrid:
        """
        shop_grid = self.shop_grid

        shop_general_items = ShopItemGrid_250814(
            shop_grid,
            templates={},
            template_area=(25, 20, 82, 72),
            amount_area=(42, 50, 65, 65),
            cost_area=(-12, 115, 60, 155),
            price_area=(14, 121, 85, 150),
        )
        shop_general_items.load_template_folder(self.shop_template_folder)
        shop_general_items.load_cost_template_folder('./assets/shop/cost')
        return shop_general_items

    def shop_items(self):
        """
        Shared alias for all shops
        If there are server-lang
        differences, reference
        shop_guild/medal for @Config
        example

        Returns:
            ShopItemGrid:
        """
        return self.shop_general_items

    currency_rechecked = 0

    def shop_currency(self):
        """
        Ocr shop guild currency if needed
        (gold coins and gems)
        Then return gold coin count

        Returns:
            int: gold coin amount
        """
        while 1:
            self._currency = self.status_get_gold_coins()
            self.gems = self.status_get_gems()
            logger.info(f'Gold coins: {self._currency}, Gems: {self.gems}')

            if self.currency_rechecked >= 3:
                logger.warning('Failed to handle fix currency bug in general shop, skip')
                break

            # if self._currency == 0 and self.gems == 0:
            #     logger.info('Game bugged, coins and gems disappeared, switch between shops to reset')
            #     self.currency_rechecked += 1
            #
            #     # 2022.06.01 General shop no longer at an expected location
            #     # NavBar 'get_active' (0 index-based) and swap with its left
            #     # adjacent neighbor then back (NavBar 'set' is 1 index-based)
            #     index = self._shop_bottom_navbar.get_active(self)
            #     self.shop_bottom_navbar_ensure(left=index)
            #     self.shop_bottom_navbar_ensure(left=index + 1)
            #     continue
            # else:
            #     break
            # 2023.07.13 Shop UI changed entirely, remove all these
            break

        return self._currency

    def shop_check_item(self, item):
        """
        Args:
            item: Item to check

        Returns:
            bool: whether item can be bought
        """
        if item.cost == 'Coins':
            if item.price > self._currency:
                return False
            return True

        if self.config.GeneralShop_UseGems:
            if item.cost == 'Gems':
                if item.price > self.gems:
                    return False
                return True

        return False

    def shop_check_custom_item(self, item):
        """
        Check a custom item that should be bought with specific option.

        Args:
            item: Item to check

        Returns:
            bool: whether item is custom
        """
        if self.config.GeneralShop_ConsumeCoins and self._currency >= 550000:
            if item.cost == 'Coins':
                return True

        if self.config.GeneralShop_BuySkinBox:
            if self._is_skin_box(item):
                # check a custom item that cannot be template matched as color
                # and design constantly changes i.e. equip skin box
                logger.info(f'Item {item} is considered to be an equip skin box')
                if self._currency >= item.price:
                    return True

        return False

    _skin_box_quota_path = 'ShopFrequent.Storage.Storage.SkinBoxQuota'

    @staticmethod
    def _is_skin_box(item):
        # BoxIrisT2 / BoxSardegnaT2 are ordinary equipment research support
        # crates (e.g. 900 coins), not equip skins. Keep the upstream heuristic.
        return (
            not item.is_known_item() and item.amount == 1
            and item.cost == 'Coins' and item.price == 7000
        )

    def _skin_box_settings(self):
        """Reload current settings before selecting or recording a purchase."""
        self.config.update()
        slots = parse_skin_box_slots(self.config.GeneralShop_SkinBoxSlots)
        limit = skin_box_counter(self.config.GeneralShop_SkinBoxPurchaseLimit)
        count = skin_box_counter(self.config.GeneralShop_SkinBoxPurchaseCount)
        quota = self.config.cross_get(self._skin_box_quota_path, {})
        if not isinstance(quota, dict):
            raise ValueError('Invalid skin-box quota state')
        quota = dict(quota)
        if quota.get('stopped') and self.config.GeneralShop_BuySkinBox:
            # Also supports explicitly re-enabling in a config file. GUI
            # re-enabling resets the count/cycle via save_callback instead.
            count = 0
            quota = {'epoch': random_id(), 'stopped': False}
            with self.config.multi_set():
                self.config.GeneralShop_SkinBoxPurchaseCount = count
                self.config.cross_set(self._skin_box_quota_path, quota)
        if limit and count >= limit:
            if not quota.get('stopped') or self.config.GeneralShop_BuySkinBox:
                quota['stopped'] = True
                with self.config.multi_set():
                    self.config.GeneralShop_BuySkinBox = False
                    self.config.cross_set(self._skin_box_quota_path, quota)
        return slots, limit, count, quota

    def shop_get_item_to_buy(self, items):
        """Apply fixed positions and quota before every skin-box purchase path.

        Args:
            items (list[Item]): Detected unsold shop items.

        Returns:
            Item: Item to buy, or None.
        """
        try:
            slots, limit, count, quota = self._skin_box_settings()
            blocked = quota.get('stopped', False) or bool(limit and count >= limit)
        except ValueError as error:
            logger.warning(f'Skip equip skin boxes: {error}')
            slots, blocked = frozenset(), True
        blocked = blocked or getattr(self, '_skin_box_uncertain', False)
        buttons = {self.shop_grid[(slot - 1) % 5, (slot - 1) // 5].button for slot in slots}
        allowed = []
        for item in items:
            if self._is_skin_box(item):
                eligible = not blocked and item.button in buttons
                if not eligible:
                    logger.info(f'Skip equip skin box excluded by positions or quota: {item}')
                    continue
            allowed.append(item)
        # Sold-out slots disappear from items. Never use the remaining list's
        # indices, and never let the filter or spilled coins bypass this gate.
        return super().shop_get_item_to_buy(allowed)

    def shop_buy_execute(self, item, skip_first_screenshot=True):
        """Track one operation, counting only the clerk's confirmed receipt."""
        if not self._is_skin_box(item):
            return super().shop_buy_execute(item, skip_first_screenshot)
        # Recheck after loading currency and before interacting with the item.
        if self.shop_get_item_to_buy([item]) is not item:
            return False
        quota = self.config.cross_get(self._skin_box_quota_path, {})
        operation = {'epoch': quota.get('epoch'), 'recorded': False}
        self._skin_box_operation = operation
        try:
            return super().shop_buy_execute(item, skip_first_screenshot)
        finally:
            if not operation['recorded']:
                # An info bar or unrelated popup can end the legacy buy loop.
                # Preserve the quota and stop cosmetics for this run when the
                # outcome is uncertain; ordinary goods may still be selected.
                self._skin_box_uncertain = True
            self._skin_box_operation = None

    def shop_buy_confirmed(self, item):
        """Persist one confirmed operation; never overwrite a newer user reset."""
        operation = getattr(self, '_skin_box_operation', None)
        if not operation or operation['recorded'] or not self._is_skin_box(item):
            return
        operation['recorded'] = True
        try:
            # A new position selection affects future purchases, not accounting
            # for the confirmed operation already submitted under the old one.
            self.config.update()
            count = skin_box_counter(self.config.GeneralShop_SkinBoxPurchaseCount)
            quota = self.config.cross_get(self._skin_box_quota_path, {})
            if not isinstance(quota, dict):
                raise ValueError('Invalid skin-box quota state')
            quota = dict(quota)
        except ValueError as error:
            logger.warning(f'Cannot update skin-box counter: {error}')
            self._skin_box_uncertain = True
            return
        if operation['epoch'] != quota.get('epoch'):
            logger.info('Skin-box counter was reset during the purchase; preserve the new cycle')
            return
        try:
            limit = skin_box_counter(self.config.GeneralShop_SkinBoxPurchaseLimit)
        except ValueError:
            # Preserve the successful count even if an invalid new limit was
            # saved mid-purchase. It must not allow any more cosmetics.
            limit = 0
            self._skin_box_uncertain = True
            logger.warning('Invalid skin-box limit; record this receipt and stop further skin boxes')
        count += 1
        reached = bool(limit and count >= limit)
        if reached:
            quota['stopped'] = True
        with self.config.multi_set():
            self.config.GeneralShop_SkinBoxPurchaseCount = count
            if reached:
                self.config.GeneralShop_BuySkinBox = False
            self.config.cross_set(self._skin_box_quota_path, quota)
        logger.info(f'Confirmed skin-box purchase operations: {count}, limit: {limit or "unlimited"}')

    def run(self):
        """
        Run General Shop
        """
        # Base case; exit run if filter empty
        if not self.shop_filter:
            return

        # When called, expected to be in
        # corrected General Shop interface
        logger.hr('General Shop', level=1)

        # Execute buy operations
        # Refresh if enabled and available
        refresh = self.config.GeneralShop_Refresh
        for _ in range(2):
            success = self.shop_buy()
            if not success:
                break
            if refresh and self.shop_refresh():
                continue
            break
