from module.campaign.campaign_base import CampaignBase
from module.campaign.run import CampaignRun
from module.combat.assets import BATTLE_PREPARATION
from module.equipment.assets import *
from module.equipment.equipment_change import EquipmentChange
from module.equipment.fleet_equipment import OCR_FLEET_INDEX
from module.exception import CampaignEnd
from module.logger import logger
from module.map.assets import FLEET_PREPARATION, MAP_PREPARATION, FLEET_ENTER_FLAGSHIP_HARD_1, \
    FLEET_ENTER_FLAGSHIP_HARD_2, FLEET_ENTER_HARD_1, FLEET_ENTER_HARD_2
from module.retire.assets import DOCK_CHECK, TEMPLATE_BOGUE, TEMPLATE_HERMES, TEMPLATE_LANGLEY, TEMPLATE_RANGER
from module.retire.dock import Dock
from module.retire.scanner import ShipScanner
from module.ui.page import page_fleet, page_event
from module.ui.ui import BACK_ARROW
import inflection

SIM_VALUE = 0.95


class GemsCampaignOverride(CampaignBase):

    def handle_combat_low_emotion(self):
        """
        Overwrite info_handler.handle_combat_low_emotion()
        If GEMS_LOW_EMOTION_WITHDRAW is True, withdraw combat and change flag ship
        """
        if self.config.GemsFarming_LowEmotionRetreat:
            if not self.emotion.is_ignore:
                return False
            if self.handle_popup_cancel('IGNORE_LOW_EMOTION'):
                self.config.GEMS_EMOTION_TRIGGRED = True
                logger.hr('EMOTION WITHDRAW')

                while 1:
                    self.device.screenshot()

                    if self.handle_popup_cancel('IGNORE_LOW_EMOTION'):
                        continue

                    if self.appear(BATTLE_PREPARATION, offset=(20, 20), interval=2):
                        self.device.click(BACK_ARROW)

                    if self.is_in_map():
                        self.withdraw()
                        break

                    if self.appear(FLEET_PREPARATION, offset=(20, 20), interval=2) \
                            or self.appear(MAP_PREPARATION, offset=(20, 20), interval=2):
                        self.enter_map_cancel()
                        break
                raise CampaignEnd('Emotion withdraw')
        else:
            return super().handle_combat_low_emotion()


class GemsFarming(CampaignRun, Dock, EquipmentChange):

    def event_hard_mode_override(self):
        HARDMODEMAPS = [
            'c1', 'c2', 'c3',
            'd1', 'd2', 'd3',
            'ht1', 'ht2', 'ht3', 'ht4', 'ht5'
        ]
        if inflection.underscore(self.config.Campaign_Name) in HARDMODEMAPS:
            logger.info('Is in hard mode, switch ship changing method.')
            self._ship_detail_enter = self._ship_detail_enter_hard
            self._fleet_detail_enter = self._fleet_detail_enter_hard
            self.page_fleet_check_button = FLEET_PREPARATION
            if self.config.GemsFarming_FleetNumberInHardMode == 1:
                self.FLEET_ENTER_FLAGSHIP = FLEET_ENTER_FLAGSHIP_HARD_1
                self.FLEET_ENTER = FLEET_ENTER_HARD_1
            elif self.config.GemsFarming_FleetNumberInHardMode == 2:
                self.FLEET_ENTER_FLAGSHIP = FLEET_ENTER_FLAGSHIP_HARD_2
                self.FLEET_ENTER = FLEET_ENTER_HARD_2
            else:
                logger.critical('Fleet number to change not set, check your settings')
                from module.exception import RequestHumanTakeover
                raise RequestHumanTakeover
            self.hard_mode = True
        else:
            self._ship_detail_enter = self._ship_detail_enter
            self._fleet_detail_enter = self._fleet_detail_enter
            self.page_fleet_check_button = page_fleet.check_button
            self.FLEET_ENTER_FLAGSHIP = FLEET_ENTER_FLAGSHIP
            self.FLEET_ENTER = FLEET_ENTER
            self.hard_mode = False

    def load_campaign(self, name, folder='campaign_main'):
        super().load_campaign(name, folder)

        class GemsCampaign(GemsCampaignOverride, self.module.Campaign):
            pass

        self.campaign = GemsCampaign(device=self.campaign.device, config=self.campaign.config)

    def _fleet_detail_enter(self):
        """
        Enter GEMS_FLEET_1 page
        """
        self.ui_ensure(page_fleet)
        self.ui_ensure_index(self.config.Fleet_Fleet1, letter=OCR_FLEET_INDEX,
                             next_button=FLEET_NEXT, prev_button=FLEET_PREV, skip_first_screenshot=True)

    def _ship_detail_enter(self, button):
        self._fleet_detail_enter()
        self.equip_enter(button)

    def _fleet_detail_enter_hard(self):
        self.campaign.ensure_campaign_ui(self.stage)
        button_area = self.campaign.ENTRANCE.button
        button = Button(area=button_area, color=(0, 0, 0), button=button_area)
        self.device.click(button)
        self.ui_click(click_button=MAP_PREPARATION, check_button=FLEET_PREPARATION)

    def _ship_detail_enter_hard(self, button):
        self._fleet_detail_enter_hard()
        self.equip_enter(button)

    def flagship_change(self):
        """
        Change flagship and flagship's equipment
        If config.GemsFarming_CommonCV == 'any', only change auxiliary equipment

        Returns:
            bool: True if flagship changed.
        """

        if self.config.GemsFarming_CommonCV == 'any':
            index_list = range(3, 5)
        else:
            index_list = range(0, 5)
        logger.hr('CHANGING FLAGSHIP.')
        if self.config.GemsFarming_FlagshipEquipChange:
            logger.info('Record flagship equipment.')
            self._ship_detail_enter(self.FLEET_ENTER_FLAGSHIP)
            self.record_equipment(index_list=index_list)
            self._equip_take_off_one()
            self.ui_back(self.page_fleet_check_button)

        self._fleet_detail_enter()

        success = self.flagship_change_execute()

        if self.config.GemsFarming_FlagshipEquipChange:
            logger.info('Record flagship equipment.')
            self._ship_detail_enter(self.FLEET_ENTER_FLAGSHIP)
            self._equip_take_off_one()

            self.equipment_take_on(index_list=index_list)
            self.ui_back(self.page_fleet_check_button)

        return success

    def vanguard_change(self):
        """
        Change vanguard and vanguard's equipment

        Returns:
            bool: True if vanguard changed
        """
        logger.hr('CHANGING VANGUARD.')
        if self.config.GemsFarming_VanguardEquipChange:
            logger.info('Record vanguard equipment.')
            self._ship_detail_enter(self.FLEET_ENTER)
            self.record_equipment()
            self._equip_take_off_one()
            self.ui_back(self.page_fleet_check_button)

        self._fleet_detail_enter()

        success = self.vanguard_change_execute()

        if self.config.GemsFarming_VanguardEquipChange:
            logger.info('Equip vanguard equipment.')
            self._ship_detail_enter(self.FLEET_ENTER)
            self._equip_take_off_one()

            self.equipment_take_on()
            self.ui_back(self.page_fleet_check_button)

        return success

    def _ship_change_confirm(self, button):

        self.dock_select_one(button)
        self.dock_filter_set()
        self.dock_select_confirm(check_button=self.page_fleet_check_button)

    def get_common_rarity_cv(self):
        """
        Get a common rarity cv by config.GemsFarming_CommonCV
        If config.GemsFarming_CommonCV == 'any', return a common lv1 ~ lv33 cv
        Returns:
            Ship:
        """

        logger.hr('FINDING FLAGSHIP')

        scanner = ShipScanner(
            level=(1, 31), emotion=(10, 150), fleet=self.config.Fleet_Fleet1, status='free')
        scanner.disable('rarity')

        if not self.server_support_status_fleet_scan():
            logger.info(f'Server {self.config.SERVER} does not yet support status and fleet scanning')
            logger.info('Please contact the developer to improve as soon as possible')
            scanner.disable('status', 'fleet')
            scanner.set_limitation(level=(1, 1))

        if self.config.GemsFarming_CommonCV == 'any':
            logger.info('')

            self.dock_sort_method_dsc_set(False)

            ships = scanner.scan(self.device.image)
            if ships:
                # Don't need to change current
                return ships

            scanner.set_limitation(fleet=0)
            return scanner.scan(self.device.image, output=False)

        else:
            template = {
                'BOGUE': TEMPLATE_BOGUE,
                'HERMES': TEMPLATE_HERMES,
                'LANGLEY': TEMPLATE_LANGLEY,
                'RANGER': TEMPLATE_RANGER
            }[f'{self.config.GemsFarming_CommonCV.upper()}']

            self.dock_sort_method_dsc_set()

            ships = scanner.scan(self.device.image)
            if ships:
                # Don't need to change current
                return ships

            scanner.set_limitation(fleet=0)
            candidates = [ship for ship in scanner.scan(self.device.image, output=False)
                          if template.match(self.image_crop(ship.button), similarity=SIM_VALUE)]

            if candidates:
                return candidates

            logger.info('No specific CV was found, try reversed order.')
            self.dock_sort_method_dsc_set(False)

            candidates = [ship for ship in scanner.scan(self.device.image)
                          if template.match(self.image_crop(ship.button), similarity=SIM_VALUE)]

            return candidates

    def get_common_rarity_dd(self):
        """
        Get a common rarity dd with level is 100 (70 for servers except CN) and emotion > 10
        Returns:
            Ship:
        """
        logger.hr('FINDING VANGUARD')

        if self.config.SERVER in ['cn']:
            max_level = 100
        else:
            max_level = 70
        from module.gg_handler.gg_data import GGData
        _ggdata = GGData(self.config).get_data()
        from module.config.utils import deep_get
        _allow_low_level = deep_get(d=self.config.data,
                                    keys='GameManager.GGHandler.AllowLowLevelInGemsFarming',
                                    default=False)
        if _ggdata['gg_enable'] and _ggdata['gg_auto'] and _allow_low_level:
            min_level = 2
        else:
            min_level = max_level
        if self.hard_mode:
            min_level = max(min_level, 49)
        scanner = ShipScanner(level=(min_level, max_level), emotion=(10, 150),
                              fleet=self.config.Fleet_Fleet1, status='free')
        scanner.disable('rarity')

        if not self.server_support_status_fleet_scan():
            scanner.disable('status', 'fleet')

        ships = scanner.scan(self.device.image)
        if ships:
            # Don't need to change current
            return ships

        scanner.set_limitation(fleet=0)
        return scanner.scan(self.device.image, output=False)

    def flagship_change_execute(self):
        """
        Returns:
            bool: If success.

        Pages:
            in: page_fleet
            out: page_fleet
        """
        self.ui_click(self.FLEET_ENTER_FLAGSHIP,
                      appear_button=self.page_fleet_check_button, check_button=DOCK_CHECK, skip_first_screenshot=True)
        self.dock_filter_set(
            index='cv', rarity='common', extra='enhanceable', sort='total')
        self.dock_favourite_set(False)

        ship = self.get_common_rarity_cv()
        if ship:
            self._ship_change_confirm(min(ship, key=lambda s: (s.level, -s.emotion)).button)

            logger.info('Change flagship success')
            return True
        else:
            logger.info('Change flagship failed, no CV in common rarity.')
            self.dock_filter_set()
            self.ui_back(check_button=self.page_fleet_check_button)
            return False

    def vanguard_change_execute(self):
        """
        Returns:
            bool: If success.

        Pages:
            in: page_fleet
            out: page_fleet
        """
        self.ui_click(self.FLEET_ENTER,
                      appear_button=self.page_fleet_check_button, check_button=DOCK_CHECK, skip_first_screenshot=True)
        self.dock_filter_set(
            index='dd', rarity='common', faction='eagle', extra='can_limit_break')
        self.dock_favourite_set(False)

        ship = self.get_common_rarity_dd()
        if ship:
            self._ship_change_confirm(max(ship, key=lambda s: s.emotion).button)

            logger.info('Change vanguard ship success')
            return True
        else:
            logger.info('Change vanguard ship failed, no DD in common rarity.')
            self.dock_filter_set()
            self.ui_back(check_button=self.page_fleet_check_button)
            return False

    _trigger_lv32 = False
    _trigger_emotion = False

    def triggered_stop_condition(self, oil_check=True):
        # Lv32 limit
        if self.config.GemsFarming_FlagshipChange and self.campaign.config.LV32_TRIGGERED:
            self._trigger_lv32 = True
            logger.hr('TRIGGERED LV32 LIMIT')
            return True

        if self.campaign.map_is_auto_search and self.campaign.config.GEMS_EMOTION_TRIGGRED:
            self._trigger_emotion = True
            logger.hr('TRIGGERED EMOTION LIMIT')
            return True

        return super().triggered_stop_condition(oil_check=oil_check)

    def run(self, name, folder='campaign_main', mode='normal', total=0):
        """
        Args:
            name (str): Name of .py file.
            folder (str): Name of the file folder under campaign.
            mode (str): `normal` or `hard`
            total (int):
        """
        self.campaign_floder = folder
        self.config.STOP_IF_REACH_LV32 = self.config.GemsFarming_FlagshipChange
        self.config.RETIRE_KEEP_COMMON_CV = True
        self.event_hard_mode_override()
        while 1:
            self._trigger_lv32 = False
            is_limit = self.config.StopCondition_RunCount

            try:
                super().run(name=name, folder=folder, total=total)
            except CampaignEnd as e:
                if e.args[0] == 'Emotion withdraw':
                    self._trigger_emotion = True
                else:
                    raise e

            # End
            if self._trigger_lv32 or self._trigger_emotion:
                success = self.flagship_change()

                if self.config.GemsFarming_LowEmotionRetreat and self.config.GemsFarming_VanguardChange:
                    success = success and self.vanguard_change()

                if is_limit and self.config.StopCondition_RunCount <= 0:
                    logger.hr('Triggered stop condition: Run count')
                    self.config.StopCondition_RunCount = 0
                    self.config.Scheduler_Enable = False
                    break

                self._trigger_lv32 = False
                self._trigger_emotion = False
                self.campaign.config.LV32_TRIGGERED = False
                self.campaign.config.GEMS_EMOTION_TRIGGRED = False

                # Scheduler
                if self.config.task_switched():
                    self.campaign.ensure_auto_search_exit()
                    self.config.task_stop()
                elif not success:
                    self.campaign.ensure_auto_search_exit()
                    self.config.task_delay(minute=30)
                    self.config.task_stop()

                continue
            else:
                break

    def server_support_status_fleet_scan(self) -> bool:
        return self.config.SERVER in ['cn', 'en', 'jp']
