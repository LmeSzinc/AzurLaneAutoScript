from module.event_hospital.clue import HospitalClue
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


if __name__ == '__main__':
    self = Hospital('alas')
    self.device.screenshot()
    self.loop_invest()
