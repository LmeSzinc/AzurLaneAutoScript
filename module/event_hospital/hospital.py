from module.base.timer import Timer
from module.base.utils import random_rectangle_vector
from module.config.config import TaskEnd
from module.event_hospital.assets import *
from module.event_hospital.clue import HospitalClue
from module.event_hospital.combat import HospitalCombat
from module.exception import OilExhausted, ScriptEnd
from module.logger import logger
from module.ui.page import page_hospital
from module.ui.switch import Switch


class HospitalSwitch(Switch):
    def appear(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            bool
        """
        for data in self.state_list:
            if main.image_color_count(data['check_button'], color=(33, 77, 189), threshold=221, count=100):
                return True

        return False

    def get(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            str: state name or 'unknown'.
        """
        for data in self.state_list:
            if main.image_color_count(data['check_button'], color=(33, 77, 189), threshold=221, count=100):
                return data['state']

        return 'unknown'


HOSPITAL_TAB = HospitalSwitch('HOSPITAL_ASIDE', is_selector=True)
HOSPITAL_TAB.add_state('LOCATION', check_button=TAB_LOCATION)
HOSPITAL_TAB.add_state('CHARACTER', check_button=TAB_CHARACTER)


class Hospital(HospitalClue, HospitalCombat):
    def daily_red_dot_appear(self):
        return self.image_color_count(DAILY_RED_DOT, color=(189, 69, 66), threshold=221, count=35)

    def daily_reward_receive_appear(self):
        return self.image_color_count(DAILY_REWARD_RECEIVE, color=(41, 73, 198), threshold=221, count=200)

    def is_in_daily_reward(self, interval=0):
        return self.match_template_color(HOSIPITAL_CLUE_CHECK, offset=(30, 30), interval=interval)

    def daily_reward_receive(self):
        """"
        Returns:
            bool: If received

        Pages:
            in: page_hospital
        """
        if self.daily_red_dot_appear():
            logger.info('Daily red dot appear')
        else:
            logger.info('No daily red dot')
            return False

        logger.hr('Daily reward receive', level=2)
        # Enter reward
        logger.info('Daily reward enter')
        skip_first_screenshot = True
        self.interval_clear(page_hospital.check_button)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.is_in_daily_reward():
                break
            if self.ui_page_appear(page_hospital, interval=2):
                logger.info(f'{page_hospital} -> {HOSPITAL_GOTO_DAILY}')
                self.device.click(HOSPITAL_GOTO_DAILY)
                continue

        # Claim reward
        logger.info('Daily reward receive')
        skip_first_screenshot = True
        self.interval_clear(HOSIPITAL_CLUE_CHECK)
        timeout = Timer(1.5, count=6).start()
        clicked = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if timeout.reached():
                logger.warning('Daily reward receive timeout')
                break
            if clicked and self.is_in_daily_reward():
                if not self.daily_reward_receive_appear():
                    break
            if self.is_in_daily_reward(interval=2):
                if self.daily_reward_receive_appear():
                    self.device.click(DAILY_REWARD_RECEIVE)
                    continue
            if self.handle_get_items():
                timeout.reset()
                clicked = True
                continue

        # Claim reward
        logger.info('Daily reward exit')
        skip_first_screenshot = True
        self.interval_clear(HOSIPITAL_CLUE_CHECK)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.ui_page_appear(page_hospital):
                break
            if self.is_in_daily_reward(interval=2):
                self.device.click(HOSIPITAL_CLUE_CHECK)
                logger.info(f'is_in_daily_reward -> {HOSIPITAL_CLUE_CHECK}')
                continue

        return True

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
            HOSPITAL_TAB.set('LOCATION', main=self)
            selected = self.select_aside()
            if not selected:
                break
            self.loop_invest()

        while 1:
            logger.hr('Loop hospital aside', level=1)
            HOSPITAL_TAB.set('CHARACTER', main=self)
            selected = self.select_aside()
            if not selected:
                break
            self.loop_invest()

        while 1:
            logger.hr('Loop hospital aside', level=1)
            HOSPITAL_TAB.set('CHARACTER', main=self)
            self.aside_swipe_down()
            selected = self.select_aside()
            if not selected:
                break
            self.loop_invest()

        logger.info('Loop hospital aside end')

    def aside_swipe_down(self, skip_first_screenshot=True):
        """
        Swipe til no ASIDE_NEXT_PAGE
        """
        logger.info('Aside swipe down')
        swiped = False
        interval = Timer(2, count=6)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if swiped and not self.appear(ASIDE_NEXT_PAGE, offset=(20, 20)):
                logger.info('Aside reached end')
                break
            if interval.reached():
                p1, p2 = random_rectangle_vector(
                    vector=(0, -200), box=CLUE_LIST.area, random_range=(-20, -10, 20, 10))
                self.device.swipe(p1, p2)
                interval.reset()
                swiped = True
                continue

    def run(self):
        self.ui_ensure(page_hospital)
        self.daily_reward_receive()

        self.clue_enter()
        try:
            self.loop_aside()
            # Scheduler
            self.config.task_delay(server_update=True)
        except OilExhausted:
            self.clue_exit()
            logger.hr('Triggered stop condition: Oil limit')
            self.config.task_delay(minute=(120, 240))
        except ScriptEnd as e:
            logger.hr('Script end')
            logger.info(str(e))
            self.clue_exit()
        except TaskEnd:
            self.clue_exit()
            raise


if __name__ == '__main__':
    self = Hospital('alas')
    self.device.screenshot()
    self.loop_aside()
