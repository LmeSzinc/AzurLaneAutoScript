from datetime import datetime
from time import sleep

from module.base.decorator import cached_property
from module.base.utils import random_normal_distribution_int
from module.config.config import AzurLaneConfig
from module.logger import logger

config_name = 'EmotionRecord'


class Emotion:
    total_reduced = 0

    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig):
        """
        self.config = config
        self.emotion = self.config.config
        # self.load()
        self.update()
        self.record()

    # def load(self):
    #     logger.hr('Emotion load')
    #     self.emotion.read_file(codecs.open(self.config.EMOTION_LOG, "r", "utf8"))
    #     self.update()

    def record(self):
        for index in [1, 2, 3]:
            logger.attr(f'Emotion fleet_{index}', self.emotion[config_name][f'fleet_{index}_emotion'])
        # self.emotion.write(codecs.open(self.config.CONFIG_FILE, "w+", "utf8"))
        self.config.save()

    def recover_value(self, index):
        return self.config.__getattribute__('FLEET_%s_RECOVER_PER_HOUR' % index) // 10

    def emotion_limit(self, index):
        return self.config.__getattribute__('FLEET_%s_EMOTION_LIMIT' % index)

    def recover_stop(self, index):
        return 150 if self.recover_value(index) > 3 else 119

    def update(self):
        for index in [1, 2, 3]:
            savetime = datetime.strptime(self.emotion[config_name][f'fleet_{index}_savetime'], self.config.TIME_FORMAT)
            savetime = int(savetime.timestamp())
            recover_count = int(datetime.now().timestamp() // 360 - savetime // 360)
            recover_count = 0 if recover_count < 0 else recover_count

            value = self.emotion.getint(config_name, f'fleet_{index}_emotion')

            value += self.recover_value(index=index) * recover_count
            if value > self.recover_stop(index=index):
                value = self.recover_stop(index)
            self.emotion[config_name][f'fleet_{index}_emotion'] = str(value)
            self.emotion[config_name][f'fleet_{index}_savetime'] = str(
                datetime.strftime(datetime.now(), self.config.TIME_FORMAT))

    def reduce(self, index):
        logger.hr('Emotion reduce')
        self.update()
        self.emotion[config_name][f'fleet_{index}_emotion'] = str(int(
            self.emotion[config_name][f'fleet_{index}_emotion']) - 2)
        self.total_reduced += 2
        self.record()

    def recovered_time(self, fleet=(1, 2)):
        """
        Args:
            fleet (int, tuple):
        """
        if isinstance(fleet, int):
            fleet = (fleet,)
        recover_count = [
            (self.emotion_limit(index) - int(self.emotion[config_name][f'fleet_{index}_emotion'])) \
            // self.recover_value(index) for index in fleet]
        recover_count = max(recover_count)
        recover_timestamp = datetime.now().timestamp() // 360 + recover_count + 1
        return datetime.fromtimestamp(recover_timestamp * 360)

    def emotion_triggered(self, fleet):
        """
        Args:
            fleet (int, list):

        Returns:
            bool:
        """
        if not isinstance(fleet, list):
            fleet = [fleet]
        return datetime.now() > self.recovered_time(fleet=fleet)

    def emotion_recovered(self, fleet):
        pass

    def wait(self, fleet=(1, 2)):
        """
        Args:
            fleet (int, tuple):
        """
        self.update()
        recovered_time = self.recovered_time(fleet=fleet)
        while 1:
            if datetime.now() > recovered_time:
                break

            logger.attr('Emotion recovered', recovered_time)
            self.config.EMOTION_LIMIT_TRIGGERED = True
            sleep(60)

    @cached_property
    def bug_threshold(self):
        """
        Returns:
            int:
        """
        return random_normal_distribution_int(55, 105, n=2)

    def bug_threshold_reset(self):
        """ Call this method after emotion bug triggered. """
        del self.__dict__['bug_threshold']

    def triggered_bug(self):
        """
        The game does not calculate emotion correctly, which is a bug in AzurLane.
        After a long run, we have to restart the game to update it.
        """
        logger.attr('Emotion_bug', f'{self.total_reduced}/{self.bug_threshold}')
        if self.total_reduced >= self.bug_threshold:
            self.total_reduced = 0
            self.bug_threshold_reset()
            return True

        return False
