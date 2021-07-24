from module.campaign.run import CampaignRun
from module.combat.level import LevelOcr
from module.equipment.assets import *
from module.equipment.fleet_equipment import OCR_FLEET_INDEX
from module.retire.dock import *
from module.ui.page import page_fleet


class GemsFarming(CampaignRun):
    def flagship_change(self):
        self.ui_ensure(page_fleet)
        self.ui_ensure_index(self.config.FLEET_1, letter=OCR_FLEET_INDEX,
                             next_button=FLEET_NEXT, prev_button=FLEET_PREV, skip_first_screenshot=True)
        self.flagship_change_execute()

    def get_common_rarity_cv(self):
        """
        Returns:
            Button:
        """
        DOCK_SCROLL.total -= 14  # The bottom of the scroll is covered.
        if DOCK_SCROLL.appear(main=self):
            DOCK_SCROLL.set_bottom(main=self, skip_first_screenshot=True)
            grids = CARD_BOTTOM_LEVEL_GRIDS
        else:
            grids = CARD_LEVEL_GRIDS
        DOCK_SCROLL.total += 14  # Revert

        ocr = LevelOcr(grids.buttons, name='DOCK_LEVEL_OCR')
        list_level = ocr.ocr(self.device.image)
        for button, level in zip(grids.buttons, list_level):
            if level == 1:
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
        self.dock_filter_set_faster(index='cv', rarity='common', extra='enhanceable')

        self.device.screenshot()
        ship = self.get_common_rarity_cv()
        if ship is not None:
            self.dock_select_one(ship)
            self.dock_filter_set_faster()
            self.dock_select_confirm(check_button=page_fleet.check_button)
            logger.info('Change flagship success')
            return True
        else:
            logger.info('Change flagship failed, no CV in common rarity.')
            self.dock_filter_set_faster()
            self.ui_back(check_button=page_fleet.check_button)
            return False

    _trigger_lv32 = False

    def triggered_stop_condition(self, oil_check=True):
        # Lv32 limit
        if self.config.STOP_IF_REACH_LV32 and self.campaign.config.LV32_TRIGGERED:
            self._trigger_lv32 = True
            logger.hr('Triggered lv32 limit')
            return True

        return super().triggered_stop_condition(oil_check=oil_check)

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
