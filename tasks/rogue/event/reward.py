from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import DigitCounter
from tasks.base.assets.assets_base_popup import GET_REWARD
from tasks.combat.interact import CombatInteract
from tasks.rogue.assets.assets_rogue_reward import OCR_REMAIN, REWARD_CLOSE, USE_IMMERSIFIER, USE_STAMINA
from tasks.rogue.bleesing.ui import RogueUI


class RogueReward(RogueUI, CombatInteract):
    def _reward_update_stamina(self, skip_first_screenshot=True):
        ocr = DigitCounter(OCR_REMAIN)
        timeout = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            stamina = (0, 0, 0)
            immersifier = (0, 0, 0)

            if timeout.reached():
                logger.warning('_reward_update_stamina() timeout')
                break

            for row in ocr.detect_and_ocr(self.device.image):
                if row.ocr_text.isdigit():
                    continue
                if row.ocr_text == '+':
                    continue
                data = ocr.format_result(row.ocr_text)
                if data[2] == self.config.stored.TrailblazePower.FIXED_TOTAL:
                    stamina = data
                if data[2] == self.config.stored.Immersifier.FIXED_TOTAL:
                    immersifier = data

            if stamina[2] > 0 and immersifier[2] > 0:
                break

        stamina = stamina[0]
        immersifier = immersifier[0]
        logger.attr('TrailblazePower', stamina)
        logger.attr('Imersifier', immersifier)
        with self.config.multi_set():
            self.config.stored.TrailblazePower.value = stamina
            self.config.stored.Immersifier.value = immersifier

    def claim_domain_reward(
            self,
            use_trailblaze_power=False,
            use_immersifier=True,
            skip_first_screenshot=True
    ):
        """
        Pages:
            in: page_main, DUNGEON_COMBAT_INTERACT, near immersifier
        """
        logger.hr('Claim domain reward', level=2)
        logger.info(f'use_trailblaze_power={use_trailblaze_power}, use_immersifier={use_immersifier}')
        if not use_trailblaze_power and not use_immersifier:
            return

        confirm = Timer(0.6, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.is_in_main():
                if confirm.reached():
                    break
            else:
                confirm.reset()

            if self.handle_combat_interact():
                self.interval_clear(USE_STAMINA)
                confirm.reset()
                continue
            if self.handle_reward():
                self.interval_clear(USE_STAMINA)
                confirm.reset()
                continue
            if self.appear(REWARD_CLOSE, interval=2):
                self._reward_update_stamina()
                if use_immersifier and self.config.stored.Immersifier.value > 0:
                    self.device.click(USE_IMMERSIFIER)
                    self.interval_reset(USE_STAMINA)
                    self.interval_clear(GET_REWARD)
                    confirm.reset()
                    continue
                elif use_trailblaze_power and self.config.stored.TrailblazePower.value >= 40:
                    self.device.click(USE_STAMINA)
                    self.interval_reset(USE_STAMINA)
                    self.interval_clear(GET_REWARD)
                    confirm.reset()
                    continue
                else:
                    logger.info('Cannot claim more rewards')
                    self.device.click(REWARD_CLOSE)
                    self.interval_reset(USE_STAMINA)
                    confirm.reset()
                    break

    def can_claim_domain_reward(
            self,
            use_trailblaze_power=False,
            use_immersifier=True
    ):
        if not use_trailblaze_power and not use_immersifier:
            return False
        if use_immersifier and self.config.stored.Immersifier.value > 0:
            return True
        if use_trailblaze_power and self.config.stored.TrailblazePower.predict_current() >= 40:
            return True
        return False
