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
            logger.hr('Loop invest', level=2)
            invest = next(self.iter_invest(), None)
            if invest is None:
                logger.info('No more invest')
                break

            self.invest_enter(invest)
            self.hospital_combat()

        self.claim_invest_reward()
        logger.info('Loop invest end')

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


if __name__ == '__main__':
    self = Hospital('alas')
    self.device.screenshot()
    self.loop_invest()
