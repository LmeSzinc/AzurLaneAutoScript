from typing import List, Tuple

from module.logger import logger
from module.shop_event.clerk import EventShopClerk
from module.shop_event.item import EventShopItem, UR_SHIP_PRICES_IN_URPT, COIN_PRICE_IN_URPT, URPT_PRICE_IN_PT
from module.shop_event.selector import EVENT_SHOP_PRESET_FILTER, FILTER


class EventShop(EventShopClerk):
    """
    Class for Event Shop operations with backend operations.
    """
    pt = 0
    urpt = 0
    pt_preserved = 0

    def get_current_pts(self):
        self.pt = self.event_shop_get_pt()
        if self.event_shop_has_urpt:
            self.urpt = self.event_shop_get_urpt()

    def preserve_pt(self, amount: int):
        """
        Preserve pt for future use.
        """
        self.pt_preserved += amount
        logger.info(f"Preserved {amount} pt for future use. Total preserved pt: {self.pt_preserved}")

    def handle_items_related_with_urpt(self, items: List[EventShopItem], num_of_ships_to_buy: int = 2) -> Tuple[
        List[EventShopItem], List[EventShopItem]]:
        """
        Buy items (currently only ships) with URpt and buy URpt if necessary.

        Should be called first before buying other items, and should not be called again after buying other items.

        Returns:
            Tuple[List[EventShopItem], List[EventShopItem]]:
            A tuple of two lists:
            - The first list contains other normal items that are not related to URpt.
            - The second list contains special items that are related to URpt (URpt, coins), that should be dealt with at last.
        """
        ship_items = []
        urpt_items = []
        coin_items = []
        other_items = []

        for item in items:
            if item.price in UR_SHIP_PRICES_IN_URPT and item.cost == "URpt":
                ship_items.append(item)
            elif item.price == COIN_PRICE_IN_URPT and item.cost == "URpt":
                coin_items.append(item)
            elif item.price == URPT_PRICE_IN_PT and item.cost == "pt":
                urpt_items.append(item)
            else:
                other_items.append(item)

        # Buy ships first.
        urpt_preserve = False
        ship_items.sort(key=lambda item: item.price)
        if ship_items and num_of_ships_to_buy > 0:
            if len(ship_items) == 1 and num_of_ships_to_buy == 1:
                logger.info("Only one ship item available and num_of_ships_to_buy is 1, skipping buying ships.")
            else:
                ships_to_buy = ship_items[:num_of_ships_to_buy]
                logger.info(f"Attempting to buy ship items: {[str(item) for item in ships_to_buy]}")
                # Check URpt sufficiency.
                # If URpt is sufficient to buy all ships, should buy required number.
                # If URpt is insufficient and event shop is not ended, preserve pt to buy URpt, and buy as many ships as possible.
                # If URpt is insufficient and event shop is ended, try to buy URpt with current pt, then buy ships.
                # If URpt is still insufficient, skip buying the most expensive ship and retry.
                current_urpt = self.event_shop_get_urpt()

                while ships_to_buy:
                    urpt_needed = sum([item.price for item in ships_to_buy])
                    if current_urpt >= urpt_needed:
                        for item in ships_to_buy:
                            self.event_shop_buy_item(item)
                        logger.info(f"Successfully bought ship items: {[str(item) for item in ships_to_buy]}")
                        break
                    else:
                        if self.is_event_ended:
                            urpt_in_stock = urpt_items[0].count if urpt_items else 0
                            if current_urpt + urpt_in_stock >= urpt_needed:
                                if urpt_in_stock > 0:
                                    self.event_shop_buy_item(urpt_items[0], amount=urpt_needed - current_urpt)
                                    urpt_items[0].count -= (urpt_needed - current_urpt)
                                for item in ships_to_buy:
                                    self.event_shop_buy_item(item)
                                logger.info(f"Successfully bought ship items: {[str(item) for item in ships_to_buy]}")
                                break
                            else:
                                logger.warning(
                                    f"Insufficient URpt to buy ships: {[str(item) for item in ships_to_buy]}. Skipping the most expensive one and retrying.")
                                ships_to_buy.pop()
                        else:
                            urpt_in_stock = urpt_items[0].count if urpt_items else 0
                            if current_urpt + urpt_in_stock >= urpt_needed:
                                pt_needed = (urpt_needed - current_urpt) * URPT_PRICE_IN_PT
                                self.preserve_pt(pt_needed)
                                logger.info(f"Preserved {pt_needed} pt to buy URpt for ships.")
                                urpt_preserve = True
                                while len(ships_to_buy) > 0 and sum([item.price for item in ships_to_buy]) > current_urpt:
                                    ships_to_buy.pop()
                                if ships_to_buy:
                                    for item in ships_to_buy:
                                        self.event_shop_buy_item(item)
                                    logger.info(
                                        f"Successfully bought ship items: {[str(item) for item in ships_to_buy]}")
                                    break
                                else:
                                    logger.warning("No ships can be bought with current URpt. Skipping buying ships.")
                                    break
                            else:
                                logger.warning("Insufficient URpt to buy ships even after buying all URpt in stock. Skipping buying the most expensive ship.")
                                ships_to_buy.pop()

        if urpt_preserve:
            logger.info("Skipping buying URpt and coins due to URpt preservation for ships.")
            return other_items, []
        else:
            logger.info("Buy URpt and URpt-priced coins last.")
            return other_items, urpt_items + coin_items

    def handle_unobtained_items(self, items: List[EventShopItem], buy_unobtained_items=False) -> Tuple[List[EventShopItem], List[EventShopItem]]:
        """
        Buy all items (ships) with tag "unobtained" in the event shop.
        This should be done after handling URpt-related items but before buying other items.

        For items with stock more than 1, should buy only one and let filter string decide whether to buy more.
        The second return value will contain items with stock more than 1 that have been bought once,
        so that the caller can (and maybe should) rescan the shop.

        Args:
            items (List[EventShopItem]): List of items to buy.
            buy_unobtained_items (bool): Whether to buy unobtained items. Default is False.
        """
        if not buy_unobtained_items:
            return items, []
        unobtained_items = []
        other_items = []
        for item in items:
            if item.tag == "unobtained":
                unobtained_items.append(item)
            else:
                other_items.append(item)
        if not unobtained_items:
            return other_items, []
        if not self.is_event_ended:
            logger.info("Event is not ended, preserve pt for unobtained items. May also wait for event level drop.")
            self.preserve_pt(sum(item.price for item in unobtained_items))
            return other_items, []

        multiple_items = []
        logger.info(f"Attempting to buy unobtained items: {[str(item) for item in unobtained_items]}")
        for item in unobtained_items:
            self.event_shop_buy_item(item)
            logger.info(f"Successfully bought unobtained item: {str(item)}")
            if item.count > 1:
                item.count -= 1
                multiple_items.append(item)
            else:
                # If the item has stock 1, it won't appear in the rescan.
                pass

        return items, multiple_items

    def calculate_affordable_amount(self, item: EventShopItem) -> int:
        if item.name == "Oil":
            current_oil = self.get_oil()
            return min(item.count, (self.pt - self.pt_preserved) // item.price, (25000 - current_oil) // 1000)
        if item.cost == 'URpt':
            return min(item.count, self.urpt // item.price)
        elif item.cost == 'pt':
            return min(item.count, (self.pt - self.pt_preserved) // item.price)
        else:
            logger.error(f"Unknown cost type: {item.cost} for item: {str(item)}")
            return 0

    def run(self):
        """
        Pages:
            in: shop_event
        """
        self.event_shop_load_ensure()
        items = self.scan_all()
        if not len(items):
            logger.warning("No items found in event shop.")
            return True
        logger.hr("Event Shop buy", level=2)
        self.get_current_pts()
        items, urpt_related_items = self.handle_items_related_with_urpt(items, self.config.EventShop_BuyURShip)
        self.get_current_pts()
        items, unobtained_multiple_stock_items = self.handle_unobtained_items(items, self.config.EventShop_UnlockSSRShip)
        items += unobtained_multiple_stock_items

        if self.config.EventShop_PresetFilter == 'custom':
            filter = self.config.EventShop_CustomFilter
        else:
            filter = EVENT_SHOP_PRESET_FILTER[self.config.EventShop_PresetFilter]
        FILTER.load(filter)
        items = FILTER.apply(items)
        items += urpt_related_items
        if not len(items):
            logger.info("No items to buy after filtering.")
            return True
        logger.attr('Item_sort', ' > '.join([str(item) for item in items]))
        self.get_current_pts()
        logger.attr("Pt_preserved", self.pt_preserved)
        for item in items:
            logger.hr(f"Attempting to buy item: {str(item)}", level=3)
            affordable_amount = self.calculate_affordable_amount(item)
            if affordable_amount <= 0:
                logger.warning(f"Cannot afford to buy any of item: {str(item)}.")
                if self.is_event_ended:
                    logger.info("Event is ended, skip this item and continue to try buying other items.")
                    continue
                else:
                    logger.info("Event is not ended, stopping further purchases to avoid overspending.")
                    break
            elif affordable_amount < item.count:
                logger.warning(f"Can only afford to buy {affordable_amount} of item: {str(item)}.")
                self.event_shop_buy_item(item, amount=affordable_amount)
                if self.is_event_ended:
                    logger.info("Event is ended, continue to try buying other items.")
                    self.get_current_pts()
                    continue
                else:
                    logger.info("Event is not ended, stopping further purchases to avoid overspending.")
                    break
            else:
                self.event_shop_buy_item(item)
                logger.info(f"Successfully bought item: {str(item)}")
                self.get_current_pts()
        return True

