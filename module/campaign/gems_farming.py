from campaign.campaign_hard.campaign_hard import Config
from numpy.core.fromnumeric import sort
from module.campaign.run import CampaignRun
from module.combat.level import LevelOcr
from module.ocr.ocr import Digit
from module.equipment.assets import *
from module.equipment.fleet_equipment import OCR_FLEET_INDEX
from module.retire.dock import *
from module.ui.page import page_fleet


from module.equipment.equipment_change import EquipmentChange

SIM_VALUE = 0.95


class GemsFarming(CampaignRun, EquipmentChange):

    def _fleet_detail_enter(self):
        self.ui_ensure(page_fleet)
        self.ui_ensure_index(self.config.FLEET_1, letter=OCR_FLEET_INDEX,
                             next_button=FLEET_NEXT, prev_button=FLEET_PREV)

    def _ship_detail_enter(self, button):
        self._fleet_detail_enter()
        self.equip_enter(button)

    def flagship_change(self):
        self._ship_detail_enter(FLEET_ENTER_FLAGSHIP)
        self.record_equipment()
        self._equip_take_off_one()

        self._fleet_detail_enter()

        self.flagship_change_execute()

        self._ship_detail_enter(FLEET_ENTER_FLAGSHIP)
        self._equip_take_off_one()

        self.equipment_take_on()
    
    def vanguard_change(self):
        self._ship_detail_enter(FLEET_ENTER)
        self.record_equipment()
        self._equip_take_off_one()

        self._fleet_detail_enter()

        self.vanguard_change_execute()

        self._ship_detail_enter(FLEET_ENTER)
        self._equip_take_off_one()

        self.equipment_take_on()

    def _ship_change_confirm(self, button):

        self.dock_select_one(button)
        self.dock_filter_set_faster()
        self.dock_select_confirm(check_button=page_fleet.check_button)

    def get_common_rarity_cv(self):
        """
        Returns:
            Button:
        """

        level_grids = CARD_LEVEL_GRIDS
        card_grids = CARD_GRIDS

        template = globals()[f'TEMPLATE_{self.config.COMMON_CV_NAME}']

        self.dock_sort_method_dsc_set()

        ocr = LevelOcr(level_grids.buttons, name='DOCK_LEVEL_OCR')
        list_level = ocr.ocr(self.device.image)

        for button, level in zip(card_grids.buttons, list_level):
            if level == 1 and template.match(self.device.image.crop(button.area), similarity=SIM_VALUE):
                return button

        self.dock_sort_method_dsc_set(False)

        list_level = ocr.ocr(self.device.image)

        for button, level in zip(card_grids.buttons, list_level):
            if level == 1 and template.match(self.device.image.crop(button.area), similarity=SIM_VALUE):
                return button

        return None

    def get_common_rarity_dd(self):
        """
        Returns:
            Button:
        """

        level_grids = CARD_LEVEL_GRIDS
        card_grids = CARD_GRIDS
        emotion_grids = CARD_EMOTION_GRIDS


        level_ocr = LevelOcr(level_grids.buttons, name='DOCK_LEVEL_OCR', threshold=64)
        list_level = level_ocr.ocr(self.device.image)
        emotion_ocr = Digit(emotion_grids.buttons, name='DOCK_EMOTION_OCR', threshold=176)
        list_emotion = emotion_ocr.ocr(self.device.image)

        for button, level, emotion in list(zip(card_grids.buttons, list_level, list_emotion))[::-1]:
            if level == 100 and emotion == 150:
                return button

        return None

    def flagship_change_execute(self):
        """
        Returns:
            bool: If success.

        Pages:
            in: page_fleet
            out: page_fleet
        """
        self.ui_click(FLEET_ENTER_FLAGSHIP,
                      appear_button=page_fleet.check_button, check_button=DOCK_CHECK, skip_first_screenshot=True)
        self.dock_filter_set_faster(
            index='cv', rarity='common', extra='enhanceable', sort='total')
        self.dock_favourite_set(False)

        self.device.screenshot()
        ship = self.get_common_rarity_cv()
        if ship is not None:
            self._ship_change_confirm(ship)

            logger.info('Change flagship success')
            return True
        else:
            logger.info('Change flagship failed, no CV in common rarity.')
            self.dock_filter_set_faster()
            self.ui_back(check_button=page_fleet.check_button)
            return False
    
    _trigger_lv32 = False
    _trigger_emotion = False

    def triggered_stop_condition(self, oil_check=True):
        # Lv32 limit
        if self.config.STOP_IF_REACH_LV32 and self.campaign.config.LV32_TRIGGERED:
            self._trigger_lv32 = True
            logger.hr('Triggered lv32 limit')
            return True
        
        if self.config.GEMS_AUTO_SEARCH_FARMING and self.campaign.config.GEMS_EMOTION_TRIGGRED:
            self._trigger_emotion = True
            logger.hr('Triggered emotion limit')
            return True

        return super().triggered_stop_condition(oil_check=oil_check)

    @Config.when(GEMS_AUTO_SEARCH_FARMING = True)
    def run(self, name, folder='campaign_main', total=0):
        name = name.lower()
        if not name[0].isdigit():
            folder = self.config.EVENT_NAME
        else:
            name = 'campaign_' + name.replace('-', '_')

        while 1:
            backup = self.config.cover(
                STOP_IF_REACH_LV32=True,
                FLEET_1=self.config.GEMS_FLEET_1,
                FLEET_2=self.config.GEMS_FLEET_2,
                FLEET_BOSS=1,
                SUBMARINE=0,
                FLEET_1_FORMATION=1,
                FLEET_2_FORMATION=1,
                FLEET_1_AUTO_MODE='combat_auto',
                FLEET_2_AUTO_MODE='combat_auto',
                ENABLE_MAP_FLEET_LOCK=True,
                ENABLE_AUTO_SEARCH=True,
                ENABLE_2X_BOOK=False,
                STOP_IF_MAP_REACH='no',
                ENABLE_EMOTION_REDUCE=False,
                IGNORE_LOW_EMOTION_WARN=True,
                GEMS_AUTO_SEARCH_FARMING = True,
            )
            self._trigger_lv32 = False
            
            super().run(name=name, folder=folder, total=total)

            # End
            if self._trigger_lv32 or self._trigger_emotion:
                self.flagship_change()
                self.vanguard_change()
                self._trigger_lv32 = False
                self._trigger_emotion = False
                self.campaign.config.LV32_TRIGGERED = False
                self.campaign.config.GEMS_LEVEL_CHECK = False
                continue
            else:
                backup.recover()
                break

    def run(self, name, folder='campaign_main', total=0):
        name = name.lower()
        if not name[0].isdigit():
            folder = self.config.EVENT_NAME
        else:
            name = 'campaign_' + name.replace('-', '_')

        while 1:
            backup = self.config.cover(
                STOP_IF_REACH_LV32=True,
                FLEET_1=self.config.GEMS_FLEET_1,
                FLEET_2=self.config.GEMS_FLEET_2,
                FLEET_BOSS=1,
                SUBMARINE=0,
                FLEET_1_FORMATION=1,
                FLEET_2_FORMATION=1,
                FLEET_1_AUTO_MODE='combat_auto',
                FLEET_2_AUTO_MODE='combat_auto',
                ENABLE_MAP_FLEET_LOCK=True,
                ENABLE_AUTO_SEARCH=False,
                ENABLE_2X_BOOK=False,
                STOP_IF_MAP_REACH='no',
                ENABLE_EMOTION_REDUCE=False,
                IGNORE_LOW_EMOTION_WARN=True,
            )
            self._trigger_lv32 = False
            
            super().run(name=name, folder=folder, total=total)

            # End
            if self._trigger_lv32:
                self.flagship_change()
                self._trigger_lv32 = False
                self.campaign.config.LV32_TRIGGERED = False
                backup.recover()
                continue
            else:
                backup.recover()
                break
       
    def vanguard_change_execute(self):
        """
        Returns:
            bool: If success.

        Pages:
            in: page_fleet
            out: page_fleet
        """
        self.ui_click(FLEET_ENTER,
                      appear_button=page_fleet.check_button, check_button=DOCK_CHECK, skip_first_screenshot=True)
        self.dock_filter_set_faster(
            index='dd', rarity='common', faction='eagle')
        self.dock_favourite_set(False)

        self.device.screenshot()
        ship = self.get_common_rarity_dd()
        if ship is not None:
            self._ship_change_confirm(ship)

            logger.info('Change vanguard ship success')
            return True
        else:
            logger.info('Change vanguard ship failed, no DD in common rarity.')
            self.dock_filter_set_faster()
            self.ui_back(check_button=page_fleet.check_button)
            return False


if __name__ == '__main__':
    from module.config.config import AzurLaneConfig
    from module.device.device import Device
    config = AzurLaneConfig('alas_cn')
    az = GemsFarming(config, Device(config=config))
    az.device.screenshot()
    # az.flagship_change()
    az.flagship_change()
    az.vanguard_change()
