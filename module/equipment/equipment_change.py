from module.base.button import ButtonGrid
from module.base.decorator import Config
from module.base.utils import *
from module.equipment.assets import *
from module.equipment.equipment import Equipment
from module.ui.scroll import Scroll

EQUIP_INFO_BAR = ButtonGrid(
    origin=(723, 111), delta=(94, 0), button_shape=(76, 76), grid_shape=(5, 1), name="EQUIP_INFO_BAR"
)

EQUIPMENT_SCROLL = Scroll(EQUIP_SCROLL, color=(
    247, 211, 66), name='EQUIP_SCROLL')

SIM_VALUE = 0.90


class EquipmentChange(Equipment):

    def __init__(self, config, device):
        super().__init__(config, device=device)
        self.equip_list = {}

    def record_equipment(self, index_list=range(0, 5), skip_first_screenshot=True):
        '''
        Record equipment through upgrade page
        Notice: The equipment icons in the upgrade page are the same size as the icons in the equipment status
        '''

        self.equip_side_navbar_ensure(bottom=1)

        for index in index_list:

            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                if self.appear(EQUIPMENT_OPEN, interval=3):
                    self.device.click(EQUIP_INFO_BAR[(index, 0)])
                    # time.sleep(1)
                    continue
                if self.appear_then_click(UPGRADE_ENTER, interval=3):
                    continue
                if self.appear(UPGRADE_ENTER_CHECK, interval=3):
                    self.wait_until_stable(EQUIP_SAVE)
                    self.equip_list[index] = self.image_area(EQUIP_SAVE)
                    self.device.click(UPGRADE_QUIT)
                    self.wait_until_stable(UPGRADE_QUIT)
                    break

    def equipment_take_on(self, index_list=range(0, 5), skip_first_screenshot=True):
        '''
        Equip the equipment previously recorded
        '''

        self.equip_side_navbar_ensure(bottom=2)

        self.ensure_no_info_bar(1)

        for index in index_list:

            enter_button = globals()[
                'EQUIP_TAKE_ON_{index}'.format(index=index)]

            self.ui_click(enter_button, check_button=EQUIPPING_ON,
                          skip_first_screenshot=skip_first_screenshot, offset=(5, 5))
            self._find_equip(index)
            self.wait_until_stable(UPGRADE_QUIT)

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

    def _equip_equipment(self, point, offset=(100, 100), skip_first_screenshot=True):
        '''
        Equip Equipment then back to ship details
        Pages:
            in: EQUIPMENT STATUS
            out: SHIP_SIDEBAR_EQUIPMENT
        '''

        have_equipped = False

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if not have_equipped and self.appear(EQUIPPING_OFF, interval=5):
                self.device.click(
                    Button(button=(point[0], point[1], point[0]+offset[0], point[1]+offset[1]), color=None, area=None))
                have_equipped = True
                continue
            if have_equipped and self.appear_then_click(EQUIP_CONFIRM, interval=2):
                continue
            if self.info_bar_count():
                self.wait_until_stable(UPGRADE_QUIT)
                break

    def _find_equip(self, index):
        '''
        Find the equipment previously recorded 
        Pages:
            in: EQUIPMENT STATUS
        '''
        self.wait_until_stable(UPGRADE_QUIT, skip_first_screenshot=False)

        self.equipping_set(False)

        res = cv2.matchTemplate(np.array(self.device.screenshot()), np.array(
            self.equip_list[index]), cv2.TM_CCOEFF_NORMED)
        _, sim, _, point = cv2.minMaxLoc(res)

        if sim > SIM_VALUE:
            self._equip_equipment(point)
            return

        for _ in range(0, 15):
            self._equipment_swipe()

            res = cv2.matchTemplate(np.array(self.device.screenshot()), np.array(
                self.equip_list[index]), cv2.TM_CCOEFF_NORMED)
            _, sim, _, point = cv2.minMaxLoc(res)

            if sim > SIM_VALUE:
                self._equip_equipment(point)
                break
            if self.appear(EQUIPMENT_SCROLL_BOTTOM):
                print(23333)
                break

        return
