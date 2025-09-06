from module.base.timer import Timer
from module.base.utils import area_offset, crop, rgb2gray
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2
from module.exception import ScriptError
from module.handler.assets import GET_MISSION, POPUP_CANCEL
from module.logger import logger
from module.os.globe_operation import GlobeOperation
from module.os.globe_zone import ZoneManager
from module.os_handler.assets import *
from module.storage.assets import BOX_USE
from module.ui.scroll import Scroll

SCROLL_STORAGE = Scroll(STORATE_SCROLL, color=(247, 211, 66))


class StorageHandler(GlobeOperation, ZoneManager):
    def is_in_storage(self):
        return self.appear(STORAGE_CHECK, offset=(20, 20))

    def storage_enter(self, skip_first_screenshot=True):
        """
        Pages:
            in: is_in_map, STORAGE_ENTER
            out: STORAGE_CHECK
        """
        logger.info('Storage enter')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_storage():
                break

            if self.appear_then_click(STORAGE_ENTER, offset=(200, 5), interval=3):
                continue
            # A game bug that AUTO_SEARCH_REWARD from the last cleared zone popups
            if self.appear_then_click(AUTO_SEARCH_REWARD, offset=(50, 50), interval=3):
                continue
            if self.handle_map_event():
                continue

        self.handle_info_bar()

    def storage_quit(self):
        """
        Pages:
            in: STORAGE_CHECK
            out: is_in_map
        """
        logger.info('Storage quit')
        self.ui_back(STORAGE_ENTER, offset=(200, 5), skip_first_screenshot=True)

    def _storage_item_use(self, button, skip_first_screenshot=True):
        """
        Args:
            button (Button): Item
            skip_first_screenshot (bool):

        Pages:
            in: STORAGE_CHECK
            out: STORAGE_CHECK
        """
        success = False
        get_mission_counter = 0
        self.interval_clear(STORAGE_CHECK)
        self.interval_clear(STORAGE_USE)
        self.interval_clear(GET_ITEMS_1)
        self.interval_clear(GET_ITEMS_2)
        self.interval_clear(GET_ADAPTABILITY)
        self.interval_clear(GET_MISSION)

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Accidentally clicked on an item, having popups for its info
            if self.appear(GET_MISSION, offset=True, interval=2):
                logger.info(f'_storage_item_use item info -> {GET_MISSION}')
                self.device.click(GET_MISSION)
                self.interval_reset(STORAGE_CHECK)
                get_mission_counter += 1
                if get_mission_counter >= 3:
                    logger.warning('Possibly stuck on energy storage device, redetecting logger items.')
                    break
                continue
            # Item rewards
            if self.appear_then_click(STORAGE_USE, offset=(180, 30), interval=5):
                self.interval_reset(STORAGE_CHECK)
                continue
            if self.appear_then_click(BOX_USE, offset=(180, 30), interval=5):
                self.interval_reset(STORAGE_CHECK)
                success = True
                continue
            if self.appear_then_click(GET_ITEMS_1, interval=5):
                self.interval_reset(STORAGE_CHECK)
                success = True
                continue
            if self.appear_then_click(GET_ITEMS_2, interval=5):
                self.interval_reset(STORAGE_CHECK)
                success = True
                continue
            if self.appear(GET_ADAPTABILITY, offset=5, interval=2):
                self.device.click(CLICK_SAFE_AREA)
                success = True
                continue
            # Use item
            if self.appear(STORAGE_CHECK, offset=(20, 20), interval=5):
                self.device.click(button)
                continue

            # End
            if success and self.appear(STORAGE_CHECK, offset=(20, 20)):
                break

    def storage_logger_use_all(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Pages:
            in: STORAGE_CHECK
            out: STORAGE_CHECK, scroll to bottom
        """
        logger.hr('Storage logger use all')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if SCROLL_STORAGE.appear(main=self):
                SCROLL_STORAGE.set_bottom(main=self, skip_first_screenshot=True)

            image = rgb2gray(self.device.image)
            items = TEMPLATE_STORAGE_LOGGER.match_multi(image, similarity=0.5)
            items.extend(TEMPLATE_STORAGE_LOGGER_UNLOCK.match_multi(image, similarity=0.75))
            logger.attr('Storage_logger', len(items))

            if len(items):
                self._storage_item_use(items[0])
                continue
            else:
                logger.info('All loggers in storage have been used')
                break

    def logger_use(self, quit=True):
        logger.hr('Logger use')
        self.storage_enter()
        self.storage_logger_use_all()
        if quit:
            self.storage_quit()

    def storage_sample_use_all(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Pages:
            in: STORAGE_CHECK
            out: STORAGE_CHECK, scroll to bottom
        """
        sample_types = [
            TEMPLATE_STORAGE_OFFENSE, TEMPLATE_STORAGE_SURVIVAL, TEMPLATE_STORAGE_COMBAT,
            TEMPLATE_STORAGE_QUALITY_OFFENSE, TEMPLATE_STORAGE_QUALITY_SURVIVAL, TEMPLATE_STORAGE_QUALITY_COMBAT
        ]
        for sample_type in sample_types:
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                image = rgb2gray(self.device.image)
                items = sample_type.match_multi(image, similarity=0.75)
                logger.attr('Storage_sample', len(items))

                if len(items):
                    self._storage_item_use(items[0])
                else:
                    break
        logger.info('All samples in storage have been used')

    def tuning_sample_use(self, quit=True):
        logger.hr('Turning sample use')
        self.storage_enter()
        self.storage_sample_use_all()
        if quit:
            self.storage_quit()

    def repair_ship_select(self, button, skip_first_screenshot=True):
        """
        Args:
            button (Button): Ship
            skip_first_screenshot:

        Returns:
            bool: if selected

        Pages:
            in: STORAGE_FLEET_CHOOSE
            out: STORAGE_FLEET_CHOOSE
        """
        # click area above hp bar to avoid click effects
        click_area = (button.area[0] + 40, button.area[1] - 100, button.area[2] - 10, button.area[3] - 50)
        click_button = Button(area=click_area, color=(0, 0, 0), button=click_area, name='STORAGE_SHIP_SELECT')
        timeout = Timer(5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            image = self.image_crop(area_offset(button.area, (0, 10)), copy=False)
            # End
            # blue background for area below hp bar means ship selected
            if self.image_color_count(image, color=(93, 148, 203), count=300):
                logger.info('Storage Ship Selected')
                self.interval_clear(STORAGE_FLEET_CHOOSE)
                return True
            if timeout.reached():
                logger.warning('Wait storage ship select timeout')
                self.interval_clear(STORAGE_FLEET_CHOOSE)
                return False

            if self.appear(STORAGE_FLEET_CHOOSE, offset=(20, 20), interval=2):
                self.device.click(click_button)
                continue

    def repair_pack_use_confirm(self, button, skip_first_screenshot=True):
        """
        Args:
            button (Button): Ship
            skip_first_screenshot:

        Pages:
            in: STORAGE_FLEET_CHOOSE
            out: STORAGE_FLEET_CHOOSE
        """
        self.interval_clear(POPUP_CANCEL)
        self.device.click_record_clear()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            image = self.image_crop(area_offset(button.area, (0, 10)), copy=False)
            # End
            if self.appear(STORAGE_REPAIR_CONFIRM, offset=(20, 20)) and \
                    not self.image_color_count(image, color=(93, 148, 203), count=300):
                logger.info('Ship Fixed')
                break
            if self.handle_popup_cancel('STORAGE_REPAIR_FULL_CANCEL'):
                logger.info('No need to fix this ship')
                break

            if self.appear_then_click(STORAGE_REPAIR_CONFIRM, offset=(20, 20)):
                continue


    def repair_pack_use(self, button):
        """
        Select a ship that needs to be repaired, then use repair packs

        Args:
            button (Button): Ship

        Pages:
            in: STORAGE_FLEET_CHOOSE
            out: STORAGE_FLEET_CHOOSE
        """
        self.repair_ship_select(button)
        self.repair_pack_use_confirm(button)

    def storage_repair_cancel(self):
        """
        Pages:
            in: STORAGE_FLEET_CHOOSE
            out: STORAGE_CHECK
        """
        self.ui_click(STORAGE_REPAIR_CANCEL, STORAGE_CHECK, retry_wait=2, skip_first_screenshot=True)

    def _storage_coordinate_checkout(self, button, types=('OBSCURE',), skip_first_screenshot=True):
        """
        Args:
            button (Button): Item
            types (tuple[str]):
            skip_first_screenshot (bool):

        Pages:
            in: STORAGE_CHECK
            out: is_in_map, in an obscure zone, or STORAGE_FLEET_CHOOSE.
        """
        self.interval_clear([
            STORAGE_CHECK,
            STORAGE_COORDINATE_CHECKOUT
        ])
        self.popup_interval_clear()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(STORAGE_CHECK, offset=(30, 30), interval=5):
                self.device.click(button)
                continue
            if self.appear_then_click(STORAGE_COORDINATE_CHECKOUT, offset=(30, 30), interval=5):
                self.interval_reset(STORAGE_CHECK)
                continue
            if self.handle_popup_confirm('STORAGE_CHECKOUT'):
                # Submarine popup
                continue

            # End
            if self.is_zone_pinned():
                break
            if types[0] == 'REPAIR_PACK' and self.appear(STORAGE_FLEET_CHOOSE, offset=(20, 20)):
                return

        self.zone_type_select(types)
        self.globe_enter(zone=self.name_to_zone(72))

    @staticmethod
    def _storage_item_to_template(item):
        """
        Args:
            item (str): 'OBSCURE', 'ABYSSAL' or 'REPAIR_PACK'.

        Returns:
            Template:
        """
        if item == 'OBSCURE':
            return TEMPLATE_STORAGE_OBSCURE
        elif item == 'ABYSSAL':
            return TEMPLATE_STORAGE_ABYSSAL
        elif item == 'REPAIR_PACK':
            return TEMPLATE_STORAGE_REPAIR_PACK
        else:
            raise ScriptError(f'Unknown storage item: {item}')

    def storage_checkout_item(self, item, skip_obscure_hazard_2=False, skip_first_screenshot=True):
        """
        Args:
            item (str): 'OBSCURE', 'ABYSSAL' or 'REPAIR_PACK'.
            skip_obscure_hazard_2: if skip hazard 2 obscure
            skip_first_screenshot:

        Returns:
            bool: If checkout

        Pages:
            in: STORAGE_CHECK
            out: is_in_map, in an obscure/abyssal zone if checkout.
                 is_in_map, in previous zone if no more obscure/abyssal coordinates.
                 STORAGE_FLEET_CHOOSE, for using repair packs.
        """
        logger.hr(f'Storage checkout item {item}')
        if SCROLL_STORAGE.appear(main=self):
            if item == 'REPAIR_PACK':
                # repair packs always at the bottom page
                SCROLL_STORAGE.set_bottom(main=self, skip_first_screenshot=skip_first_screenshot)
            else:
                SCROLL_STORAGE.set_top(main=self, skip_first_screenshot=skip_first_screenshot)

        confirm_timer = Timer(0.6, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            image = rgb2gray(self.device.image)
            items = self._storage_item_to_template(item).match_multi(image, similarity=0.75)
            logger.attr(f'Storage_{item}', len(items))

            if len(items):
                for button in items:
                    if skip_obscure_hazard_2:
                        crop_image = crop(image, area_offset(button.area, (-25, -35)), copy=False)
                        if TEMPLATE_STORAGE_OBSCURE_HAZARD_2.match(crop_image, similarity=0.92):
                            continue
                    self._storage_coordinate_checkout(button, types=(item,))
                    return True
            if confirm_timer.reached():
                logger.info(f'No more {item} items in storage')
                self.storage_quit()
                return False

    def storage_get_next_item(self, item, use_logger=True, skip_obscure_hazard_2=False):
        """
        Args:
            item (str): 'OBSCURE', 'ABYSSAL' or 'REPAIR_PACK'.
            use_logger: If use all loggers.
            skip_obscure_hazard_2: if skip hazard 2 obscure

        Returns:
            bool: If checkout

        Pages:
            in: in_map
            out: is_in_map, in an obscure/abyssal zone if checkout.
                 is_in_map, in previous zone if no more obscure/abyssal coordinates.
                 STORAGE_FLEET_CHOOSE, for using repair packs.
        """
        logger.hr('OS get next obscure')
        self.storage_enter()
        if use_logger:
            self.storage_logger_use_all()

        result = self.storage_checkout_item(item, skip_obscure_hazard_2=skip_obscure_hazard_2)
        return result
