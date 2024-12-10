from module.base.timer import Timer
from module.base.utils import get_color
from module.combat.combat import Combat
from module.freebies.assets import *
from module.logger import logger
from module.ui.assets import BATTLE_PASS_CHECK, REWARD_GOTO_BATTLE_PASS
from module.ui.page import page_reward
from module.ui.ui import UI
from module.ui_white.assets import POPUP_CONFIRM_WHITE_BATTLEPASS


class BattlePass(Combat, UI):
    def battle_pass_red_dot_appear(self):
        """
        Returns:
            bool: If appear.

        Page:
            in: page_reward
        """
        if self.appear(REWARD_GOTO_BATTLE_PASS, offset=(50, 150)):
            # Load button offset from REWARD_GOTO_BATTLE_PASS,
            # because entrance may not be the top one.
            BATTLE_PASS_RED_DOT.load_offset(REWARD_GOTO_BATTLE_PASS)
            # Not using self.appear() here, because it's transparent,
            # color may be different depending on background.
            r, _, _ = get_color(self.device.image, BATTLE_PASS_RED_DOT.button)
            if r > BATTLE_PASS_RED_DOT.color[0] - 40:
                logger.info('Found battle pass red dot')
                return True
            else:
                logger.info('No battle pass red dot')
                return False
        else:
            logger.warning('No battle pass entrance')
            return False

    def handle_battle_pass_popup(self):
        return self.appear_then_click(PURCHASE_POPUP, offset=(20, 20), interval=2)

    def battle_pass_enter(self):
        """
        Page:
            in: page_reward
            out: page_battle_pass
        """

        def appear_button():
            return self.appear(REWARD_GOTO_BATTLE_PASS, offset=(50, 150))

        self.ui_click(REWARD_GOTO_BATTLE_PASS, appear_button=appear_button, check_button=BATTLE_PASS_CHECK,
                      additional=self.handle_battle_pass_popup, skip_first_screenshot=True)

    def battle_pass_receive(self, skip_first_screenshot=True):
        """
        Returns:
            bool: If received.

        Pages:
            in: page_battle_pass
            out: page_battle_pass
        """
        logger.hr('Battle pass receive', level=1)
        self.battle_status_click_interval = 2
        confirm_timer = Timer(1, count=3).start()
        received = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(REWARD_RECEIVE, offset=(20, 20), interval=3):
                confirm_timer.reset()
                continue
            if self.match_template_color(REWARD_RECEIVE_SP, offset=(20, 20), interval=3, threshold=15):
                self.device.click(REWARD_RECEIVE_SP)
                confirm_timer.reset()
                continue
            if self.appear_then_click(REWARD_RECEIVE_WHITE, offset=(20, 20), interval=3):
                confirm_timer.reset()
                continue
            if self.handle_battle_pass_popup():
                confirm_timer.reset()
                continue
            if self.config.SERVER == 'cn':
                if self.appear_then_click(POPUP_CONFIRM_WHITE_BATTLEPASS, offset=(20, 20), interval=3):
                    confirm_timer.reset()
                    continue
            if self.handle_popup_confirm('BATTLE_PASS'):
                # Lock new META ships
                confirm_timer.reset()
                continue
            if self.handle_get_items():
                received = True
                confirm_timer.reset()
                continue
            if self.handle_get_ship():
                received = True
                confirm_timer.reset()
                continue
            if self.handle_get_skin():
                received = True
                confirm_timer.reset()
                continue

            # End
            if self.appear(BATTLE_PASS_CHECK, offset=(20, 20)) \
                    and not self.appear(REWARD_RECEIVE, offset=(20, 20)) \
                    and not self.appear(REWARD_RECEIVE_WHITE, offset=(20, 20)):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

        logger.info(f'Battle pass receive finished, received={received}')
        return received

    def run(self):
        self.ui_ensure(page_reward)

        if self.battle_pass_red_dot_appear():
            self.battle_pass_enter()
            self.battle_pass_receive()
