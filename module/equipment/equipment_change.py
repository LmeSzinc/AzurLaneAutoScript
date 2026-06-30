from module.base.button import ButtonGrid
from module.base.decorator import Config
from module.base.utils import *
from module.equipment.assets import *
from module.equipment.equipment import Equipment
from module.logger import logger
from module.ui.assets import BACK_ARROW
from module.ui.scroll import Scroll
from module.ui.switch import Switch

# Button of 5 equipments
EQUIP_INFO_BAR = ButtonGrid(
    origin=(695, 127), delta=(86.25, 0), button_shape=(73, 73), grid_shape=(5, 1), name="EQUIP_INFO_BAR")
# Bottom-left corner of EQUIP_INFO_BAR, to detect whether the grid has an equipment
EQUIPMENT_GRID = ButtonGrid(
    origin=(696, 170), delta=(86.25, 0), button_shape=(32, 32), grid_shape=(5, 1), name='EQUIPMENT_GRID')
EQUIPMENT_SCROLL = Scroll(EQUIP_SCROLL, color=(247, 211, 66), name='EQUIP_SCROLL')
SIM_VALUE = 0.90

equipping_filter = Switch('Equipping_filter')
equipping_filter.add_state('on', check_button=EQUIPPING_ON)
equipping_filter.add_state('off', check_button=EQUIPPING_OFF)


class EquipmentChange(Equipment):
    equipment_list = {}

    def equipping_set(self, enable=False):
        if equipping_filter.set('on' if enable else 'off', main=self):
            self.wait_until_stable(SWIPE_AREA)

    def ship_equipment_record_image(self, index_list=range(0, 5)):
        """
        Record equipment through upgrade page
        Notice: The equipment icons in the upgrade page are the same size as the icons in the equipment status
        """
        logger.info('RECORD EQUIPMENT')
        self.ship_side_navbar_ensure(bottom=1)

        # Ensure EQUIPMENT_GRID in the right place
        skip_first_screenshot = True
        while True:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.appear(EQUIPMENT_OPEN, offset=(5, 5)):
                break

        self.equipment_list = {}
        info_bar_disappeared = False
        for index, button in enumerate(EQUIPMENT_GRID.buttons):
            if index not in index_list:
                continue
            crop_image = self.image_crop(button, copy=False)
            edge_value = np.mean(np.abs(cv2.Sobel(crop_image, 3, 1, 1)))
            # Nothing is 0.15~1
            # +1 is 40
            # +10 is 46
            if edge_value > 10:
                # Enter equipment info
                self.ui_click(appear_button=EQUIPMENT_OPEN,
                              click_button=EQUIP_INFO_BAR[(index, 0)],
                              check_button=UPGRADE_ENTER)
                # Enter upgrade inform
                self.ui_click(click_button=UPGRADE_ENTER,
                              check_button=UPGRADE_ENTER_CHECK, skip_first_screenshot=True)
                # Save equipment template
                if not info_bar_disappeared:
                    self.handle_info_bar()
                    info_bar_disappeared = True
                self.equipment_list[index] = self.image_crop(EQUIP_SAVE)
                # Quit upgrade inform
                self.ui_click(
                    click_button=UPGRADE_QUIT, check_button=EQUIPMENT_OPEN, appear_button=UPGRADE_ENTER_CHECK,
                    skip_first_screenshot=True)
            else:
                logger.info(f"Equipment {index} is empty")

        logger.info(f"Recorded equipment index list: {list(self.equipment_list.keys())}")

    def ship_equipment_take_on_image(self, index_list=range(0, 5), skip_first_screenshot=True):
        """
        Equip the equipment previously recorded
        """
        logger.info('Take on equipment')
        self.ship_side_navbar_ensure(bottom=2)

        for index in index_list:
            if index in self.equipment_list:
                logger.info(f'Take on {index}')
                enter_button = globals()[
                    'EQUIP_TAKE_ON_{index}'.format(index=index)]

                self.ui_click(enter_button, check_button=EQUIPPING_ON,
                              skip_first_screenshot=skip_first_screenshot, offset=(5, 5))
                self.handle_info_bar()
                self._find_equipment(index)

    @Config.when(DEVICE_CONTROL_METHOD='minitouch')
    def _equipment_swipe(self, distance=190):
        # Distance of two commission is 146px
        p1, p2 = random_rectangle_vector(
            (0, -distance), box=(620, 67, 1154, 692), random_range=(-20, -5, 20, 5))
        self.device.drag(p1, p2, segments=2, shake=(25, 0),
                         point_random=(0, 0, 0, 0), shake_random=(-5, 0, 5, 0))
        self.device.sleep(0.3)
        self.device.screenshot()

    @Config.when(DEVICE_CONTROL_METHOD=None)
    def _equipment_swipe(self, distance=300):
        # Distance of two commission is 146px
        p1, p2 = random_rectangle_vector(
            (0, -distance), box=(620, 67, 1154, 692), random_range=(-20, -5, 20, 5))
        self.device.drag(p1, p2, segments=2, shake=(25, 0),
                         point_random=(0, 0, 0, 0), shake_random=(-5, 0, 5, 0))
        self.device.sleep(0.3)
        self.device.screenshot()

    def _equip_equipment(self, point, offset=(100, 100)):
        """
        Equip Equipment then back to ship details
        Confirm the popup
        Pages:
            in: EQUIPMENT STATUS
            out: SHIP_SIDEBAR_EQUIPMENT
        """
        logger.info('Equip equipment')
        button = Button(area=(), color=(), button=(point[0], point[1], point[0] + offset[0], point[1] + offset[1]),
                        name='EQUIPMENT')
        self.ui_click(appear_button=EQUIPPING_OFF, click_button=button, check_button=EQUIP_CONFIRM)
        logger.info('Equip confirm')
        self.ui_click(click_button=EQUIP_CONFIRM, check_button=SHIP_INFO_EQUIPMENT_CHECK)

    def _find_equipment(self, index):
        """
        Find the equipment previously recorded
        Pages:
            in: EQUIPMENT STATUS
        """

        self.equipping_set(False)

        res = cv2.matchTemplate(self.device.screenshot(), np.array(
            self.equipment_list[index]), cv2.TM_CCOEFF_NORMED)
        _, sim, _, point = cv2.minMaxLoc(res)

        if sim > SIM_VALUE:
            self._equip_equipment(point)
            return

        if not EQUIPMENT_SCROLL.appear(main=self):
            logger.warning('No recorded equipment was found.')
            self.ui_back(check_button=globals()[f'EQUIP_TAKE_ON_{index}'], appear_button=EQUIPPING_OFF)
            return

        for _ in range(0, 15):
            self._equipment_swipe()

            if self.appear(EQUIP_CONFIRM, offset=(20, 20), interval=2):
                self.device.click(BACK_ARROW)
                continue
            res = cv2.matchTemplate(self.device.screenshot(), np.array(
                self.equipment_list[index]), cv2.TM_CCOEFF_NORMED)
            _, sim, _, point = cv2.minMaxLoc(res)

            if sim > SIM_VALUE:
                self._equip_equipment(point)
                break
            if self.appear(EQUIPMENT_SCROLL_BOTTOM):
                logger.warning('No recorded equipment was found.')
                self.ui_back(check_button=globals()[f'EQUIP_TAKE_ON_{index}'], appear_button=EQUIPPING_OFF)
                break

        return
