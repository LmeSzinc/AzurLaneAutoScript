from datetime import datetime

import numpy as np

from module.base.decorator import cached_property
from module.campaign.campaign_base import CampaignBase
from module.campaign.run import CampaignRun
from module.combat.assets import BATTLE_PREPARATION
from module.combat.emotion import Emotion
from module.equipment.assets import *
from module.equipment.equipment import Equipment
from module.exception import CampaignEnd
from module.handler.assets import AUTO_SEARCH_MAP_OPTION_OFF
from module.logger import logger
from module.map.assets import FLEET_PREPARATION, MAP_PREPARATION
from module.ocr.ocr import Digit
from module.retire.assets import *
from module.retire.dock import Dock
from module.retire.scanner import ShipScanner
from module.ui.assets import BACK_ARROW
from module.ui.page import page_fleet


FLEET_INDEX = Digit(OCR_FLEET_INDEX, letter=(90, 154, 255), threshold=128, alphabet='123456')
SIM_VALUE = 0.92


class GemsCampaignOverride(CampaignBase):
    def handle_combat_low_emotion(self):
        """
        Overwrite info_handler.handle_combat_low_emotion()
        If change vanguard is enabled, withdraw combat and change flagship and vanguard
        """
        if self.config.GemsFarming_ChangeVanguard == 'disabled':
            result = self.handle_popup_confirm('IGNORE_LOW_EMOTION')
            if result:
                # Avoid clicking AUTO_SEARCH_MAP_OPTION_OFF
                self.interval_reset(AUTO_SEARCH_MAP_OPTION_OFF)
            return result

        if self.handle_popup_cancel('IGNORE_LOW_EMOTION'):
            self.config.GEMS_EMOTION_TRIGGERED = True
            logger.hr('EMOTION WITHDRAW')

            while 1:
                self.device.screenshot()

                if self.handle_story_skip():
                    continue
                if self.handle_popup_cancel('IGNORE_LOW_EMOTION'):
                    continue

                if self.appear(BATTLE_PREPARATION, offset=(20, 20), interval=2):
                    self.device.click(BACK_ARROW)
                    continue
                if self.handle_auto_search_exit():
                    continue
                if self.is_in_stage():
                    break

                if self.is_in_map():
                    self.withdraw()
                    break

                if self.appear(FLEET_PREPARATION, offset=(20, 50), interval=2) \
                        or self.appear(MAP_PREPARATION, offset=(20, 20), interval=2):
                    self.enter_map_cancel()
                    break
            raise CampaignEnd('Emotion withdraw')


class GemsEmotion(Emotion):
    def check_reduce(self, battle):
        """
        Override Emotion.check_reduce to trigger stop condition when emotion is too low before battle.
        """
        if not self.is_calculate:
            return

        method = self.config.Fleet_FleetOrder
        if method == 'fleet1_all_fleet2_standby':
            battle = (battle, 0)
        elif method == 'fleet1_standby_fleet2_all':
            battle = (0, battle)

        battle = tuple(np.array(battle) * self.reduce_per_battle_before_entering)
        logger.info(f'Expect emotion reduce: {battle}')

        self.update()
        self.record()
        self.show()
        recovered = max([f.get_recovered(b) for f, b in zip(self.fleets, battle)])
        if recovered > datetime.now():
            self.config.GEMS_EMOTION_TRIGGERED = True
            raise CampaignEnd('Emotion control')

    def wait(self, fleet_index):
        """
        Override Emotion.wait to trigger stop condition when emotion is too low after battle.
        """
        self.update()
        self.record()
        self.show()
        fleet = self.fleets[fleet_index - 1]
        recovered = fleet.get_recovered(expected_reduce=self.reduce_per_battle)
        if recovered > datetime.now():
            self.config.GEMS_EMOTION_TRIGGERED = True


class GemsFarming(CampaignRun, Dock):
    def load_campaign(self, name, folder='campaign_main'):
        super().load_campaign(name, folder)

        class GemsCampaign(GemsCampaignOverride, self.module.Campaign):
            @cached_property
            def emotion(self):
                return GemsEmotion(config=self.config)

        self.campaign = GemsCampaign(device=self.campaign.device, config=self.campaign.config)
        if not self.change_vanguard:
            self.campaign.config.override(Emotion_Mode='ignore')
        self.campaign.config.override(EnemyPriority_EnemyScaleBalanceWeight='S1_enemy_first')

    @property
    def change_flagship_equip(self):
        return 'equip' in self.config.GemsFarming_ChangeFlagship

    @property
    def change_vanguard(self):
        return 'ship' in self.config.GemsFarming_ChangeVanguard

    @property
    def change_vanguard_equip(self):
        return 'equip' in self.config.GemsFarming_ChangeVanguard

    @property
    def max_level(self):
        if self.config.SERVER == 'cn':
            return 100
        else:
            return 70

    @property
    def min_emotion(self):
        return (2 + self.campaign._map_battle) * self.campaign.emotion.reduce_per_battle

    _new_fleet_emotion = 0

    @property
    def fleet_to_attack_index(self):
        if self.config.Fleet_FleetOrder == 'fleet1_standby_fleet2_all':
            return self.config.Fleet_Fleet2
        else:
            return self.config.Fleet_Fleet1

    def ui_goto_fleet(self):
        self.ui_ensure(page_fleet)
        self.ui_ensure_index(self.fleet_to_attack_index,
                             letter=FLEET_INDEX,
                             next_button=FLEET_NEXT, 
                             prev_button=FLEET_PREV,
                             skip_first_screenshot=True)

    def ui_enter_ship(self, click_button, long_click=True):
        if long_click:
            enter_button_map = {
                FLEET_ENTER_FLAGSHIP: FLEET_DETAIL_ENTER_FLAGSHIP,
                FLEET_ENTER: FLEET_DETAIL_ENTER,
            }
            enter_button = enter_button_map.get(click_button)
            if enter_button is None:
                self.ship_info_enter(click_button=click_button, long_click=True, skip_first_screenshot=False)
                return

            self.ui_click(FLEET_DETAIL, appear_button=page_fleet.check_button,
                          check_button=FLEET_DETAIL_CHECK, skip_first_screenshot=True)
            self.ship_info_enter(enter_button, long_click=False)
        else:
            self.ship_info_enter(click_button=click_button, check_button=DOCK_CHECK, 
                                 long_click=False, skip_first_screenshot=False)

    def ui_leave_ship(self, check_button=None):
        if check_button is None:
            check_button = page_fleet.check_button
        if check_button == page_fleet.check_button:
            self.ui_back(check_button=[FLEET_DETAIL_CHECK, page_fleet.check_button])
            self.ui_back(check_button=page_fleet.check_button)
        else:
            self.ui_back(check_button=check_button)

    def find_candidates(self, templates, scanner: ShipScanner, output=False):
        """
        Find candidates based on template matching using a scanner.
        """
        ships = scanner.scan(self.device.image, output=output)
        if not templates:
            return ships
        candidates = []
        for ship in ships:
            for template in templates:
                if template.match(self.image_crop(ship.button, copy=False), similarity=SIM_VALUE):
                    candidates.append(ship)
                    break
        return candidates

    def get_cv_templates(self):
        """
        Get CV templates based on config.GemsFarming_CommonCV

        Returns:
            list[Template]: CV templates
        """
        if self.config.GemsFarming_CommonCV == 'any':
            return []
        else:
            templates = {
                'bogue': TEMPLATE_BOGUE,
                'hermes': TEMPLATE_HERMES,
                'langley': TEMPLATE_LANGLEY,
                'ranger': TEMPLATE_RANGER,
            }
            return [templates[self.config.GemsFarming_CommonCV]]

    def get_common_rarity_cv(self, max_level=31, min_emotion=0):
        """
        Get a common rarity cv by config.GemsFarming_CommonCV
        If config.GemsFarming_CommonCV == 'any', return a common lv1 ~ lv31 cv by default.

        Returns:
            list[Ship]: Common rarity CVs that meet the level, emotion and fleet requirements.
        """
        self.dock_favourite_set(False, wait_loading=False)
        self.dock_sort_method_dsc_set(True, wait_loading=False)
        self.dock_filter_set(index='cv', rarity='common', extra='enhanceable', sort='total')

        logger.hr('FINDING FLAGSHIP')
        templates = self.get_cv_templates()
        scanner = ShipScanner(level=(1, max_level), emotion=(min_emotion, 150), fleet=self.fleet_to_attack_index, status='free')
        scanner.disable('rarity')

        candidates = self.find_candidates(templates, scanner, output=True)
        if candidates:
            return candidates

        scanner.set_limitation(fleet=0)
        candidates = self.find_candidates(templates, scanner, output=False)
        if candidates or templates == []:
            return candidates

        logger.info('No specific CV was found, try reversed order.')
        self.dock_sort_method_dsc_set(False)
        candidates = self.find_candidates(templates, scanner, output=True)
        return candidates

    def flagship_change_execute(self):
        self.ui_enter_ship(FLEET_ENTER_FLAGSHIP, long_click=False)
        candidate = self.get_common_rarity_cv(min_emotion=self.min_emotion)
        if candidate:
            ship = max(candidate, key=lambda s: (s.level, s.emotion))
            self._new_fleet_emotion = min(ship.emotion, self._new_fleet_emotion) if self._new_fleet_emotion else ship.emotion
            self.dock_select_one(ship.button)
            self.dock_reset()
            self.dock_select_confirm(check_button=page_fleet.check_button)
            logger.info('Change flagship success')
            return True

        logger.info('Change flagship failed, no CV in common rarity.')
        self._new_fleet_emotion = 0
        self.dock_reset()
        self.ui_leave_ship()
        return False

    def flagship_change(self):
        """
        Change flagship and flagship's equipment

        Returns:
            bool: True if flagship changed.
        """
        logger.hr('Change flagship', level=1)
        logger.attr('ChangeFlagship', self.config.GemsFarming_ChangeFlagship)
        self.ui_goto_fleet()

        if self.change_flagship_equip:
            logger.hr('Unmount flagship equipments', level=2)
            self.ui_enter_ship(FLEET_ENTER_FLAGSHIP, long_click=True)
            self.ship_equipment_take_off()
            self.ui_leave_ship()

        logger.hr('Change flagship', level=2)
        success = self.flagship_change_execute()

        if self.change_flagship_equip:
            logger.hr('Mount flagship equipments', level=2)
            self.ui_enter_ship(FLEET_ENTER_FLAGSHIP, long_click=True)
            self.ship_equipment_take_on()
            self.ui_leave_ship()

        return success

    def get_dd_faction(self):
        if self.config.GemsFarming_CommonDD == 'any':
            faction = ['eagle', 'iron']
        elif self.config.GemsFarming_CommonDD == 'favourite':
            faction = 'all'
        elif self.config.GemsFarming_CommonDD == 'z20_or_z21':
            faction = 'iron'
        elif self.config.GemsFarming_CommonDD in ['aulick_or_foote', 'cassin_or_downes']:
            faction = 'eagle'
        else:
            logger.error(f'Invalid CommonDD setting: {self.config.GemsFarming_CommonDD}')
            logger.error("Default to 'eagle' and 'iron' faction.")
            faction = ['eagle', 'iron']
        return faction

    def get_dd_templates(self):
        """
        Get DD templates based on config.GemsFarming_CommonDD

        Returns:
            list[Template]: DD templates
        """
        if self.config.GemsFarming_CommonDD == 'aulick_or_foote':
            return [
                TEMPLATE_AULICK,
                TEMPLATE_FOOTE
            ]
        elif self.config.GemsFarming_CommonDD == 'cassin_or_downes':
            return [
                TEMPLATE_CASSIN_1, TEMPLATE_CASSIN_2,
                TEMPLATE_DOWNES_1, TEMPLATE_DOWNES_2
            ]
        else:
            return []

    def get_common_rarity_dd(self, min_emotion=0):
        """
        Get a common rarity dd by config.GemsFarming_CommonDD
        If config.GemsFarming_CommonDD == 'any', return a common self.max_level dd by default.

        Returns:
            list[Ship]: Common rarity DDs that meet the emotion and fleet requirements.
        """
        faction = self.get_dd_faction()
        self.dock_favourite_set(self.config.GemsFarming_CommonDD == 'favourite', wait_loading=False)
        self.dock_sort_method_dsc_set(True, wait_loading=False)
        self.dock_filter_set(index='dd', rarity='common', faction=faction, extra='can_limit_break')

        logger.hr('FINDING VANGUARD')
        templates = self.get_dd_templates()
        scanner = ShipScanner(level=(self.max_level, self.max_level), emotion=(min_emotion, 150), fleet=[0, self.fleet_to_attack_index], status='free')
        scanner.disable('rarity')

        candidates = self.find_candidates(templates, scanner, output=True)
        if candidates or templates == []:
            return candidates

        logger.info('No specific DD was found, try reversed order.')
        self.dock_sort_method_dsc_set(False)
        candidates = self.find_candidates(templates, scanner, output=True)
        return candidates

    def vanguard_change_execute(self):
        self.ui_enter_ship(FLEET_ENTER, long_click=False)
        candidate = self.get_common_rarity_dd(min_emotion=self.min_emotion)
        if candidate:
            ship = max(candidate, key=lambda s: s.emotion)
            self._new_fleet_emotion = min(ship.emotion, self._new_fleet_emotion) if self._new_fleet_emotion else ship.emotion
            self.dock_select_one(ship.button)
            self.dock_reset()
            self.dock_select_confirm(check_button=page_fleet.check_button)
            logger.info('Change vanguard success')
            return True

        logger.info('Change vanguard failed, no DD in common rarity.')
        self._new_fleet_emotion = 0
        self.dock_reset()
        self.ui_leave_ship()
        return False

    def vanguard_change(self):
        """
        Change vanguard and vanguard's equipment

        Returns:
            bool: True if vanguard changed.
        """
        logger.hr('Change vanguard', level=1)
        logger.attr('ChangeVanguard', self.config.GemsFarming_ChangeVanguard)
        self.ui_goto_fleet()

        if self.change_vanguard_equip:
            logger.hr('Unmount vanguard equipments', level=2)
            self.ui_enter_ship(FLEET_ENTER, long_click=True)
            self.ship_equipment_take_off()
            self.ui_leave_ship()

        logger.hr('Change vanguard', level=2)
        success = self.vanguard_change_execute()

        if self.change_vanguard_equip:
            logger.hr('Mount vanguard equipments', level=2)
            self.ui_enter_ship(FLEET_ENTER, long_click=True)
            self.ship_equipment_take_on()
            self.ui_leave_ship()

        return success

    _trigger_lv32: bool = False
    _trigger_emotion: bool = False

    def triggered_stop_condition(self, oil_check=True):
        # Lv32 limit
        if self.campaign.config.LV32_TRIGGERED:
            self._trigger_lv32 = True
            logger.hr('TRIGGERED LV32 LIMIT')
            return True

        if self.campaign.config.GEMS_EMOTION_TRIGGERED:
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
        self.config.override(STOP_IF_REACH_LV32=True)

        while 1:
            self._trigger_lv32 = False
            is_limit = self.config.StopCondition_RunCount

            try:
                super().run(name=name, folder=folder, total=total)
            except CampaignEnd as e:
                if "Emotion" in e.args[0]:
                    self._trigger_emotion = True
                else:
                    raise e

            # End
            if self._trigger_lv32 or self._trigger_emotion:
                self._new_fleet_emotion = 150
                success = self.flagship_change()
                if self.change_vanguard:
                    success = success and self.vanguard_change()

                if self.fleet_to_attack == 2:
                    self.campaign.config.set_record(Emotion_Fleet2Value=self._new_fleet_emotion)
                else:
                    self.campaign.config.set_record(Emotion_Fleet1Value=self._new_fleet_emotion)

                if is_limit and self.config.StopCondition_RunCount <= 0:
                    logger.hr('Triggered stop condition: Run count')
                    self.config.StopCondition_RunCount = 0
                    self.config.Scheduler_Enable = False
                    break

                self._trigger_lv32 = False
                self._trigger_emotion = False
                self.campaign.config.LV32_TRIGGERED = False
                self.campaign.config.GEMS_EMOTION_TRIGGERED = False

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
