from module.base.base import ModuleBase
from module.base.timer import Timer
from module.base.utils import color_bar_percentage
from module.combat_ui.assets import (PAUSE, PAUSE_Christmas, PAUSE_Cyber, PAUSE_HolyLight, PAUSE_Iridescent_Fantasy,
                                     PAUSE_Neon, PAUSE_New, PAUSE_Nurse, PAUSE_Pharaoh)
from module.exercise.assets import *
from module.logger import logger


class HpDaemon(ModuleBase):
    attacker_hp = 1.0
    defender_hp = 1.0
    # _last_secure_time = 0
    low_hp_confirm_timer: Timer

    @staticmethod
    def _calculate_hp(image, area, reverse=False, starter=2, prev_color=(239, 32, 33), threshold=30):
        """
        Args:
            image:
            area:
            reverse: True if HP is left align.
            starter:
            prev_color:
            threshold:

        Returns:
            float: HP. 0 to 1.
        """
        # bar = crop(image, area)
        # length = bar.shape[1]
        # bar = np.swapaxes(bar, 0, 1)
        # bar = bar[::-1, :, :] if reverse else bar
        # prev_index = 0
        # for index, color in enumerate(bar):
        #     if index < starter:
        #         continue
        #     mask = color_similar_1d(color, prev_color, threshold=30)
        #     if np.any(mask):
        #         prev_color = color[mask].mean(axis=0)
        #         prev_index = index
        #
        # return prev_index / length
        return color_bar_percentage(
            image, area, prev_color=prev_color, starter=starter, reverse=reverse, threshold=threshold)

    def _show_hp(self, low_hp_time=0):
        """
        Examples:
            [ 80% - 70%]
            [ 80% - 70%]
            [ 80% - 70%] - Low HP: 3.154s
        """
        text = '[%s - %s]' % (
            str(int(self.attacker_hp * 100)).rjust(2, '0') + '%',
            str(int(self.defender_hp * 100)).rjust(2, '0') + '%')
        if low_hp_time:
            text += ' - Low HP: %ss' % str(round(low_hp_time, 3)).ljust(5, '0')
        logger.info(text)

    def _at_low_hp(self, image, pause=PAUSE):
        if pause == PAUSE:
            self.attacker_hp = self._calculate_hp(image, area=ATTACKER_HP_AREA.area, reverse=True)
            self.defender_hp = self._calculate_hp(image, area=DEFENDER_HP_AREA.area, reverse=False)
        elif pause in [
            PAUSE_New,
            PAUSE_Iridescent_Fantasy,
            PAUSE_Neon,
            PAUSE_Christmas,
            PAUSE_Cyber,
            PAUSE_HolyLight,
            PAUSE_Pharaoh,
            PAUSE_Nurse,
        ]:
            self.attacker_hp = self._calculate_hp(image, area=ATTACKER_HP_AREA_New.area, reverse=True)
            self.defender_hp = self._calculate_hp(image, area=DEFENDER_HP_AREA_New.area, reverse=True)
        else:
            logger.warning(f'_at_low_hp received unknown pause: {pause}')
            self.attacker_hp = self._calculate_hp(image, area=ATTACKER_HP_AREA.area, reverse=True)
            self.defender_hp = self._calculate_hp(image, area=DEFENDER_HP_AREA.area, reverse=False)

        # Opponent died or HP bar get covered
        if self.defender_hp < 0.01:
            self.low_hp_confirm_timer.reset()
        if 0.01 < self.attacker_hp <= self.config.Exercise_LowHpThreshold:
            if self.low_hp_confirm_timer.reached() and self.low_hp_confirm_timer.current() < 300:
                self._show_hp(self.low_hp_confirm_timer.current())
                return True
            else:
                return False
        else:
            self.low_hp_confirm_timer.reset()
            return False
