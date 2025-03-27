from module.event_hospital.clue import HospitalClue
from module.event_hospital.assets import *
from module.event_hospital.combat import HospitalCombat
from module.logger import logger


class Hospital(HospitalClue, HospitalCombat):
    def loop_invest(self):
        """
        Do all invest in page
        """
        while 1:
            logger.hr('Loop hospital invest', level=2)
            invest = next(self.iter_invest(), None)
            if invest is None:
                logger.info('No more invest')
                break

            self.invest_enter(invest)
            self.hospital_combat()

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


if __name__ == '__main__':
    self = Hospital('alas')
    self.device.screenshot()
    self.loop_aside()
