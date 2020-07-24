import numpy as np

from module.base.timer import Timer
from module.base.utils import red_overlay_transparency, get_color
from module.combat.combat import Combat
from module.handler.assets import *
from module.logger import logger
from module.template.assets import *


def ambush_letter_preprocess(image):
    """
    Args:
        image (np.ndarray):

    Returns:
        np.ndarray
    """
    image = image.astype(float)
    image = (image - 64) / 0.75
    image[image > 255] = 255
    image[image < 0] = 0
    image = image.astype('uint8')
    return image


TEMPLATE_AMBUSH_EVADE_SUCCESS.image = ambush_letter_preprocess(TEMPLATE_AMBUSH_EVADE_SUCCESS.image)
TEMPLATE_AMBUSH_EVADE_FAILED.image = ambush_letter_preprocess(TEMPLATE_AMBUSH_EVADE_FAILED.image)
TEMPLATE_MAP_WALK_OUT_OF_STEP.image = ambush_letter_preprocess(TEMPLATE_MAP_WALK_OUT_OF_STEP.image)


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
        logger.info('Map air raid')
        disappear = Timer(self.MAP_AIR_RAID_CONFIRM_SECOND)
        disappear.start()
        while 1:
            self.device.screenshot()
            if self._air_raid_appear():
                disappear.reset()
            else:
                if disappear.reached():
                    break

    def _handle_ambush(self):
        logger.info('Map ambushed')
        self.wait_until_appear_then_click(MAP_AMBUSH_EVADE)
        # self.sleep(0.8)
        # while 1:
        #     self.screenshot()
        #     if self.handle_info_bar():
        #         if self.combat_appear():
        #             logger.info('Ambush evade failed')
        #             self.combat()
        #         break
        self.wait_until_appear(INFO_BAR_1)
        image = ambush_letter_preprocess(np.array(self.device.image.crop(INFO_BAR_DETECT.area)))

        if TEMPLATE_AMBUSH_EVADE_SUCCESS.match(image):
            logger.attr('Ambush_evade', 'success')
        elif TEMPLATE_AMBUSH_EVADE_FAILED.match(image):
            logger.attr('Ambush_evade', 'failed')
            self.combat(expected_end='no_searching')
        else:
            logger.warning('Unrecognised info when ambush evade.')
            self.ensure_no_info_bar()
            if self.combat_appear():
                self.combat()

    def handle_ambush(self):
        if not self.config.MAP_HAS_AMBUSH:
            return False

        if self._air_raid_appear():
            self._handle_air_raid()
            return True

        if self._ambush_appear():
            self._handle_ambush()
            return True

        if self.appear(MAP_AMBUSH_EVADE):
            self._handle_ambush()

        return False

    def handle_walk_out_of_step(self):
        if not self.config.MAP_HAS_FLEET_STEP:
            return False
        if not self.appear(INFO_BAR_1):
            return False

        image = ambush_letter_preprocess(np.array(self.device.image.crop(INFO_BAR_DETECT.area)))
        if TEMPLATE_MAP_WALK_OUT_OF_STEP.match(image):
            logger.warning('Map walk out of step.')
            self.handle_info_bar()
            return True

        return False
