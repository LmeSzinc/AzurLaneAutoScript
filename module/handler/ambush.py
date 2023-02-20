from module.base.timer import Timer
from module.base.utils import get_color, red_overlay_transparency
from module.combat.combat import Combat
from module.handler.assets import *
from module.handler.info_handler import info_letter_preprocess
from module.logger import logger
from module.template.assets import *

TEMPLATE_AMBUSH_EVADE_SUCCESS.pre_process = info_letter_preprocess
TEMPLATE_AMBUSH_EVADE_FAILED.pre_process = info_letter_preprocess
TEMPLATE_MAP_WALK_OUT_OF_STEP.pre_process = info_letter_preprocess


class AmbushHandler(Combat):
    MAP_AMBUSH_OVERLAY_TRANSPARENCY_THRESHOLD = 0.40
    MAP_AIR_RAID_OVERLAY_TRANSPARENCY_THRESHOLD = 0.35  # Usually (0.50, 0.53)
    MAP_AIR_RAID_CONFIRM_SECOND = 0.5

    def ambush_color_initial(self):
        MAP_AMBUSH.load_color(self.device.image)
        MAP_AIR_RAID.load_color(self.device.image)

    def _ambush_appear(self):
        return red_overlay_transparency(MAP_AMBUSH.color, get_color(self.device.image, MAP_AMBUSH.area)) > \
               self.MAP_AMBUSH_OVERLAY_TRANSPARENCY_THRESHOLD

    def _air_raid_appear(self):
        return red_overlay_transparency(MAP_AIR_RAID.color, get_color(self.device.image, MAP_AIR_RAID.area)) > \
               self.MAP_AIR_RAID_OVERLAY_TRANSPARENCY_THRESHOLD

    def _handle_air_raid(self):
        """
        Wait until air raid disappeared
        """
        logger.info('Map air raid')
        disappear = Timer(self.MAP_AIR_RAID_CONFIRM_SECOND).start()
        timeout = Timer(2.5, count=2).start()

        while 1:
            self.device.screenshot()
            # Timeout
            if timeout.reached():
                logger.warning('_handle_air_raid timeout, assume air raid disappeared')
                break
            # Disappeared
            if self._air_raid_appear():
                disappear.reset()
            else:
                if disappear.reached():
                    break

    def _handle_ambush_evade(self):
        logger.info('Map ambushed')
        # Wait MAP_AMBUSH_EVADE
        self.wait_until_appear(MAP_AMBUSH_EVADE, offset=(30, 30))
        self.handle_info_bar()

        # Click MAP_AMBUSH_EVADE
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.info_bar_count():
                break

            if self.appear_then_click(MAP_AMBUSH_EVADE, offset=(30, 30), interval=3):
                continue

        # Handle evade success and failures
        image = info_letter_preprocess(self.image_crop(INFO_BAR_DETECT))
        if TEMPLATE_AMBUSH_EVADE_SUCCESS.match(image):
            logger.attr('Ambush_evade', 'success')
        elif TEMPLATE_AMBUSH_EVADE_FAILED.match(image):
            logger.attr('Ambush_evade', 'failed')
            self.combat(expected_end='no_searching', fleet_index=self.fleet_show_index)
        else:
            logger.warning('Unrecognized info when ambush evade.')
            self.ensure_no_info_bar()
            if self.combat_appear():
                self.combat(fleet_index=self.fleet_show_index)

    def _handle_ambush_attack(self):
        logger.info('Map ambushed')
        # Wait MAP_AMBUSH_ATTACK
        self.wait_until_appear(MAP_AMBUSH_ATTACK, offset=(30, 30))

        # Click MAP_AMBUSH_ATTACK
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.combat_appear():
                break

            if self.appear_then_click(MAP_AMBUSH_ATTACK, offset=(30, 30), interval=3):
                continue
            if self.handle_combat_low_emotion():
                continue
            if self.handle_retirement():
                continue

        # In battle
        logger.attr('Ambush_evade', 'attack')
        self.combat(expected_end='no_searching', fleet_index=self.fleet_show_index)

    def _handle_ambush(self):
        if self.config.Campaign_AmbushEvade:
            return self._handle_ambush_evade()
        else:
            return self._handle_ambush_attack()

    def handle_ambush(self):
        if not self.config.MAP_HAS_AMBUSH:
            return False

        if self._air_raid_appear():
            self._handle_air_raid()
            return True

        if self._ambush_appear():
            self._handle_ambush()
            return True

        if self.appear(MAP_AMBUSH_EVADE, offset=(30, 30)):
            self._handle_ambush()

        return False

    def handle_walk_out_of_step(self):
        if not self.config.MAP_HAS_FLEET_STEP:
            return False
        if not self.info_bar_count():
            return False

        image = info_letter_preprocess(self.image_crop(INFO_BAR_DETECT))
        if TEMPLATE_MAP_WALK_OUT_OF_STEP.match(image):
            logger.warning('Map walk out of step.')
            self.handle_info_bar()
            return True

        return False
