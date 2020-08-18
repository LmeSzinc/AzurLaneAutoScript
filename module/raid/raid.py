from module.campaign.run import OCR_OIL
from module.combat.assets import *
from module.combat.combat import Combat
from module.logger import logger
from module.map.map_operation import MapOperation
from module.raid.assets import *
from module.ui.assets import RAID_CHECK


class OilExhausted(Exception):
    pass


class Raid(MapOperation, Combat):
    def combat_preparation(self, balance_hp=False, emotion_reduce=False, auto=True, fleet_index=1):
        """
        Args:
            balance_hp (bool):
            emotion_reduce (bool):
            auto (bool):
            fleet_index (int):
        """
        logger.info('Combat preparation.')
        oil_checked = False

        if emotion_reduce:
            self.emotion.wait(fleet=fleet_index)

        while 1:
            self.device.screenshot()

            if self.appear(BATTLE_PREPARATION):
                if self.handle_combat_automation_set(auto=auto):
                    continue
                if not oil_checked and self.config.STOP_IF_OIL_LOWER_THAN:
                    self.ensure_combat_oil_loaded()
                    oil = OCR_OIL.ocr(self.device.image)
                    oil_checked = True
                    if oil < self.config.STOP_IF_OIL_LOWER_THAN:
                        logger.hr('Triggered oil limit')
                        raise OilExhausted()
            if self.handle_raid_ticket_use():
                continue
            if self.handle_retirement():
                continue
            if self.handle_combat_low_emotion():
                continue
            if self.appear_then_click(BATTLE_PREPARATION, interval=2):
                continue
            if self.handle_combat_automation_confirm():
                continue
            if self.handle_story_skip():
                continue

            # End
            if self.is_combat_executing():
                if emotion_reduce:
                    self.emotion.reduce(fleet_index)
                break

    def handle_raid_ticket_use(self):
        """
        Returns:
            bool: If clicked.
        """
        if self.appear(TICKET_USE_CONFIRM, offset=(30, 30), interval=1):
            if self.config.RAID_USE_TICKET:
                self.device.click(TICKET_USE_CONFIRM)
            else:
                self.device.click(TICKET_USE_CANCEL)
            return True

        return False

    @staticmethod
    def raid_entrance(mode):
        """
        Args:
            mode (str): easy, normal, hard

        Returns:
            Button:
        """
        if mode == 'easy':
            return RAID_EASY
        elif mode == 'normal':
            return RAID_NORMAL
        elif mode == 'hard':
            return RAID_HARD
        else:
            logger.warning(f'Unknown raid mode: {mode}')
            exit(1)

    def raid_enter(self, mode):
        logger.hr('Raid Enter')
        while 1:
            self.device.screenshot()

            if self.appear_then_click(self.raid_entrance(mode), offset=(10, 10), interval=5):
                continue
            if self.appear_then_click(RAID_FLEET_PREPARATION, interval=5):
                continue

            # End
            if self.combat_appear():
                break

    def raid_expected_end(self):
        return self.appear(RAID_CHECK, offset=(30, 30))

    def raid_execute_once(self, mode):
        logger.hr('Raid Execute')
        self.raid_enter(mode=mode)
        self.combat(balance_hp=False, expected_end=self.raid_expected_end)
        logger.hr('Raid End')
