from datetime import datetime, timedelta

from module.base.timer import Timer
from module.logger import logger
from tasks.base.assets.assets_base_popup import GET_REWARD
from tasks.combat.interact import CombatInteract
from tasks.dungeon.state import DungeonState
from tasks.rogue.assets.assets_rogue_reward import REWARD_CLOSE, USE_IMMERSIFIER, USE_STAMINA
from tasks.rogue.blessing.ui import RogueUI


class RogueReward(RogueUI, CombatInteract, DungeonState):
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
        init = False
        initial_stamina = 0
        initial_immersifier = 0
        exhausted = False

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.is_in_main():
                if confirm.reached():
                    break
                if exhausted:
                    break
            else:
                confirm.reset()

            if not exhausted and self.handle_combat_interact():
                self.interval_clear(USE_STAMINA)
                confirm.reset()
                continue
            if self.handle_reward():
                self.interval_clear(USE_STAMINA)
                confirm.reset()
                continue
            if self.appear(REWARD_CLOSE, interval=2):
                self.dungeon_update_stamina()
                if not init:
                    initial_stamina = self.config.stored.TrailblazePower.value
                    initial_immersifier = self.config.stored.Immersifier.value
                    init = True
                if use_trailblaze_power and self.config.stored.TrailblazePower.value >= 40:
                    self.device.click(USE_STAMINA)
                    self.interval_reset(USE_STAMINA)
                    self.interval_clear(GET_REWARD)
                    confirm.reset()
                    continue
                elif use_immersifier and self.config.stored.Immersifier.value > 0:
                    self.device.click(USE_IMMERSIFIER)
                    self.interval_reset(USE_STAMINA)
                    self.interval_clear(GET_REWARD)
                    confirm.reset()
                    continue
                else:
                    logger.info('Cannot claim more rewards')
                    self.device.click(REWARD_CLOSE)
                    self.interval_reset(USE_STAMINA)
                    confirm.reset()
                    exhausted = True
                    continue

        with self.config.multi_set():
            claimed = 0
            diff = initial_immersifier - self.config.stored.Immersifier.value
            if diff >= 1:
                claimed += diff
                self.config.stored.Immersifier.add(-diff)
            diff = initial_stamina - self.config.stored.TrailblazePower.value
            if diff + 2 >= 40:
                # Stamina may recover while receiving
                diff = int((diff + 2) // 40)
                claimed += diff
                self.config.stored.TrailblazePower.add(-diff)
            # Clicked button, closed reward popup, planer page closed by game itself, exhausted=False, claimed once
            # Cannot claim more, clicked REWARD_CLOSE to close planer page, exhausted=True, nothing claimed at last
            if not exhausted:
                claimed += 1
                if use_trailblaze_power:
                    self.config.stored.TrailblazePower.add(-1)
                elif use_immersifier:
                    self.config.stored.Immersifier.add(-1)
            logger.info(f'Claimed planer reward {claimed} times')
            if self.config.stored.DungeonDouble.rogue > 0:
                self.config.stored.DungeonDouble.rogue -= claimed
        return claimed

    def can_claim_domain_reward(
            self,
            use_trailblaze_power=False,
            use_immersifier=True
    ):
        if not use_trailblaze_power and not use_immersifier:
            logger.info('Cannot claim domain reward, as all disabled')
            return False
        if use_immersifier:
            if self.config.stored.Immersifier.value > 0:
                logger.info(f'Can claim domain reward, got immersifiers')
                return True
            if datetime.now() - self.config.stored.Immersifier.time > timedelta(minutes=15):
                logger.info(f'Can claim domain reward, immersifier record outdated')
                return True
        if use_trailblaze_power and self.config.stored.TrailblazePower.predict_current() >= 40:
            logger.info(f'Can claim domain reward, got enough trailblaze power')
            return True
        logger.info('Cannot claim domain reward, requirements not satisfied')
        return False
