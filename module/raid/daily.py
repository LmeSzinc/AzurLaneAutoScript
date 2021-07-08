from module.logger import logger
from module.raid.raid import raid_ocr
from module.raid.run import RaidRun
from module.ui.page import page_raid

RECORD_OPTION = ('DailyRecord', 'raid')
RECORD_SINCE = (0,)


class RaidDaily(RaidRun):
    def get_remain(self, mode):
        """
        Args:
            mode (str): easy, normal, hard

        Returns:
            int:
        """
        ocr = raid_ocr(raid=self.config.RAID_NAME, mode=mode)
        remain, _, _ = ocr.ocr(self.device.image)
        logger.attr(f'{mode.capitalize()} Remain', remain)
        return remain

    def record_executed_since(self):
        return self.config.record_executed_since(option=RECORD_OPTION, since=RECORD_SINCE)

    def record_save(self):
        return self.config.record_save(option=RECORD_OPTION)

    def run(self, name=''):
        """
        Args:
            name (str): Raid name, such as 'raid_20200624'
        """
        self.reward_backup_daily_reward_settings()
        name = name if name else self.config.RAID_NAME
        self.ui_ensure(page_raid)

        if self.config.RAID_HARD:
            remain = self.get_remain(mode='hard')
            if remain > 0:
                super().run(name=name, mode='hard', total=remain)

        if self.config.RAID_NORMAL:
            remain = self.get_remain(mode='normal')
            if remain > 0:
                super().run(name=name, mode='normal', total=remain)

        if self.config.RAID_EASY:
            remain = self.get_remain(mode='easy')
            if remain > 0:
                super().run(name=name, mode='easy', total=remain)

        self.reward_recover_daily_reward_settings()
