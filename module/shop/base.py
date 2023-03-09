import re

from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.filter import Filter
from module.base.timer import Timer
from module.combat.assets import GET_ITEMS_1, GET_SHIP, GET_ITEMS_3
from module.logger import logger
from module.shop.assets import *
from module.shop.shop_select_globals import *
from module.statistics.item import ItemGrid
from module.tactical.tactical_class import Book
from module.ui.ui import UI

FILTER_REGEX = re.compile(
    '^(array|book|box|bulin|cat'
    '|chip|coin|cube|drill|food'
    '|plate|retrofit|pr|dr'
    '|logger|tuning'
    '|hecombatplan'
    '|albacore|bataan|bluegill|carabiniere|casablanca|contedicavour|dukeofyork|echo'
    '|eldridge|grenville|hibiki|hunter|kinggeorgev|kinu|kuroshio|lemalinmuse'
    '|letemeraire|littorio|newcastle|oyashio|quincy|ryuujou|sanjuan|sheffieldmuse'
    '|trento|vincennes|z26|z28|z36'
    ')'

    '(neptune|monarch|ibuki|izumo|roon|saintlouis'
    '|seattle|georgia|kitakaze|azuma|friedrich'
    '|gascogne|champagne|cheshire|drake|mainz|odin'
    '|anchorage|hakuryu|agir|august|marcopolo'
    '|plymouth|rupprecht|harbin|chkalov|brest'
    '|red|blue|yellow'
    '|general|gun|torpedo|antiair|plane|wild'
    '|dd|cl|bb|cv'
    '|abyssal|archive|obscure|unlock'
    '|combat|offense|survival)?'

    '(s[1-5]|t[1-6])?$',
    flags=re.IGNORECASE)
FILTER_ATTR = ('group', 'sub_genre', 'tier')
FILTER = Filter(FILTER_REGEX, FILTER_ATTR)


class ShopItemGrid(ItemGrid):
    def predict(self, image, name=True, amount=True, cost=False, price=False, tag=False):
        """
        Define new attributes to predicted Item obj for shop item filtering
        """
        super().predict(image, name, amount, cost, price, tag)

        for item in self.items:
            # Set defaults
            item.group, item.sub_genre, item.tier = None, None, None

            # Can use regular expression to quickly populate
            # the new attributes
            name = item.name
            result = re.search(FILTER_REGEX, name)
            if result:
                item.group, item.sub_genre, item.tier = \
                [group.lower()
                 if group is not None else None
                 for group in result.groups()]
            else:
                # if not name.isnumeric():
                #     logger.warning(f'Unable to parse shop item {name}; '
                #                     'check template asset and filter regexp')
                #     raise ScriptError
                continue

            # Sometimes book's color and/or tier will be misidentified
            # Undergo a second template match using Book class
            if item.group == 'book':
                book = Book(image, item._button)
                if item.sub_genre is not None:
                    item.sub_genre = book.genre_str
                item.tier = book.tier_str.lower()
                item.name = ''.join(
                    [part.title()
                     if part is not None
                     else ''
                     for part in [item.group, item.sub_genre, item.tier]])

        return self.items


class ShopBase(UI):
    _currency = 0
    shop_template_folder = ''

    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        return ''

    @cached_property
    def shop_grid(self):
        """
        Returns:
            ButtonGrid:
        """
        shop_grid = ButtonGrid(
            origin=(477, 152), delta=(156, 214), button_shape=(96, 96), grid_shape=(5, 2), name='SHOP_GRID')
        return shop_grid

    def shop_items(self):
        """
        Returns:
            None, base default value
            ShopItemGrid, variant value
        """
        return None

    def shop_currency(self):
        """
        Returns:
            int:
        """
        return self._currency

    def shop_has_loaded(self, items):
        """
        Custom steps for variant shop
        if needed to ensure shop has
        loaded completely
        ShopMedal for example will initially
        display default items at default prices

        Args:
            items: list[Item]

        Returns:
            bool:
        """
        return True

    def shop_detect_items(self, image=None):
        """
        Detect items on image for testing purpose
        """
        if image is None:
            image = self.device.image

        # Retrieve ShopItemGrid
        shop_items = self.shop_items()
        if shop_items is None:
            logger.warning('Expected type \'ShopItemGrid\' but was None')
            return []

        if self.config.SHOP_EXTRACT_TEMPLATE:
            if self.shop_template_folder:
                logger.info(f'Extract item templates to {self.shop_template_folder}')
                shop_items.extract_template(image, self.shop_template_folder)
            else:
                logger.warning('SHOP_EXTRACT_TEMPLATE enabled but shop_template_folder is not set, skip extracting')

        shop_items.predict(
            image,
            name=True,
            amount=False,
            cost=True,
            price=True,
            tag=False
        )

        # Log final result on predicted items
        items = shop_items.items
        grids = shop_items.grids
        if len(items):
            min_row = grids[0, 0].area[1]
            row = [str(item) for item in items if item.button[1] == min_row]
            logger.info(f'Shop row 1: {row}')
            row = [str(item) for item in items if item.button[1] != min_row]
            logger.info(f'Shop row 2: {row}')
            return items
        else:
            logger.info('No shop items found')
            return []

    def shop_obstruct_handle(self):
        """
        Remove obstructions in shop view if any

        Returns:
            bool:
        """
        # Handle shop obstructions
        if self.appear(GET_SHIP, interval=1):
            logger.info(f'Shop obstruct: {GET_SHIP} -> {SHOP_CLICK_SAFE_AREA}')
            self.device.click(SHOP_CLICK_SAFE_AREA)
            return True
        # To lock new ships
        if self.handle_popup_confirm('SHOP_OBSTRUCT'):
            return True
        if self.appear(GET_ITEMS_1, interval=1):
            logger.info(f'Shop obstruct: {GET_ITEMS_1} -> {SHOP_CLICK_SAFE_AREA}')
            self.device.click(SHOP_CLICK_SAFE_AREA)
            return True
        if self.appear(GET_ITEMS_3, interval=1):
            logger.info(f'Shop obstruct: {GET_ITEMS_3} -> {SHOP_CLICK_SAFE_AREA}')
            self.device.click(SHOP_CLICK_SAFE_AREA)
            return True

        return False

    def shop_get_items(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot (bool):

        Returns:
            list[Item]:
        """
        # Retrieve ShopItemGrid
        shop_items = self.shop_items()
        if shop_items is None:
            logger.warning('Expected type \'ShopItemGrid\' but was None')
            return []

        # Loop on predict to ensure items
        # have loaded and can accurately
        # be read
        record = 0
        timeout = Timer(3, count=9).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.shop_obstruct_handle():
                timeout.reset()
                continue

            if self.config.SHOP_EXTRACT_TEMPLATE:
                if self.shop_template_folder:
                    logger.info(f'Extract item templates to {self.shop_template_folder}')
                    shop_items.extract_template(self.device.image, self.shop_template_folder)
                else:
                    logger.warning('SHOP_EXTRACT_TEMPLATE enabled but shop_template_folder is not set, skip extracting')

            shop_items.predict(
                self.device.image,
                name=True,
                amount=False,
                cost=True,
                price=True,
                tag=False
            )

            if timeout.reached():
                logger.warning('Items loading timeout; continue and assumed has loaded')
                break

            # Check unloaded items, because AL loads items too slow.
            items = shop_items.items
            known = len([item for item in items if item.is_known_item])
            logger.attr('Item detected', known)
            if known == 0 or known != record:
                record = known
                continue
            else:
                record = known

            # End
            if self.shop_has_loaded(items):
                break

        # Log final result on predicted items
        items = shop_items.items
        grids = shop_items.grids
        if len(items):
            min_row = grids[0, 0].area[1]
            row = [str(item) for item in items if item.button[1] == min_row]
            logger.info(f'Shop row 1: {row}')
            row = [str(item) for item in items if item.button[1] != min_row]
            logger.info(f'Shop row 2: {row}')
            return items
        else:
            logger.info('No shop items found')
            return []

    def shop_check_item(self, item):
        """
        Override in variant class
        for specific check item
        actions

        Args:
            item: Item to check

        Returns:
            bool:
        """
        if item.price > self._currency:
            return False
        return True

    def shop_check_custom_item(self, item):
        """
        Override in variant class
        for specific check custom item
        actions; no restriction to filter string

        Args:
            item (Item):

        Returns:
            bool:
        """
        return False

    def shop_get_item_to_buy(self, items):
        """
        Args:
            items list(Item): acquired from shop_get_items

        Returns:
            Item: Item to buy, or None.
        """
        # First, must scan for custom items
        # as has no template or filter support
        for item in items:
            if self.shop_check_custom_item(item):
                return item

        # Second, load selection, apply filter,
        # and return 1st item in result if any
        FILTER.load(self.shop_filter)
        filtered = FILTER.apply(items, self.shop_check_item)

        if not filtered:
            return None
        logger.attr('Item_sort', ' > '.join([str(item) for item in filtered]))

        return filtered[0]
