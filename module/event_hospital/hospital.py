from module.config.config import TaskEnd
from module.event_hospital.assets import *
from module.event_hospital.clue import HospitalClue
from module.event_hospital.combat import HospitalCombat
from module.exception import OilExhausted, ScriptEnd
from module.logger import logger
from module.ui.page import page_hospital


class Hospital(HospitalClue, HospitalCombat):
    def loop_invest(self):
        """
        Do all invest in page
        """
        self.config.override(Fleet_FleetOrder='fleet1_all_fleet2_standby')
        while 1:
            logger.hr('Loop hospital invest', level=2)
            # Scheduler
            # May raise ScriptEnd
            self.emotion.check_reduce(battle=1)

            entered = self.invest_enter()
            if not entered:
                break
            self.hospital_combat()

            # Scheduler
            # May raise TaskEnd
            if self.config.task_switched():
                self.config.task_stop()

            # Aside reset after combat, so we should loop in aside again
            break

        self.claim_invest_reward()
        logger.info('Loop hospital invest end')

    def invest_reward_appear(self) -> bool:
        return self.image_color_count(INVEST_REWARD_RECEIVE, color=(33, 77, 189), threshold=221, count=100)

    def claim_invest_reward(self):
        if self.invest_reward_appear():
            logger.info('Invest reward appear')
        else:
            logger.info('No invest reward')
            return False
        # Get reward
        skip_first_screenshot = True
        clicked = True
        self.interval_clear(HOSIPITAL_CLUE_CHECK)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if clicked:
                if self.is_in_clue() and not self.invest_reward_appear():
                    return True
            if self.handle_get_items():
                clicked = True
                continue
            if self.is_in_clue(interval=2):
                if self.invest_reward_appear():
                    self.device.click(INVEST_REWARD_RECEIVE)
                    continue

    def loop_aside(self):
        """
        Do all aside in page
        """
        while 1:
            logger.hr('Loop hospital aside', level=1)
            aside = next(self.iter_aside(), None)
            if aside is None:
                logger.info('No more aside')
                break

            self.select_aside(aside)
            self.loop_invest()

        logger.info('Loop hospital aside end')

    def run(self):
        self.ui_ensure(page_hospital)
        self.clue_enter()

        try:
            self.loop_aside()
        except OilExhausted:
            self.clue_exit()
            logger.hr('Triggered stop condition: Oil limit')
            self.config.task_delay(minute=(120, 240))
        except ScriptEnd as e:
            logger.hr('Script end')
            logger.info(str(e))
            self.clue_exit()
            raise
        except TaskEnd:
            self.clue_exit()
            raise

        # Scheduler
        self.config.task_delay(server_update=True)


if __name__ == '__main__':
    self = Hospital('alas')
    self.device.screenshot()
    self.loop_aside()
