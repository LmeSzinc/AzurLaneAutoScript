import re

from module.base.filter import Filter
from module.base.timer import Timer
from module.logger import logger
from module.raid.raid import raid_ocr
from module.raid.run import RaidRun
from module.ui.page import page_raid


class RaidStage:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


STAGES = ["easy", "normal", "hard"]
STAGE_FILTER = Filter(regex=re.compile("(\w+)"), attr=["name"])


class RaidDaily(RaidRun):
    def get_remain(self, mode, skip_first_screenshot=True):
        """
        Args:
            mode (str): easy, normal, hard
            skip_first_screenshot (bool):

        Returns:
            int:
        """
        confirm_timer = Timer(0.3, count=0)
        prev = 30
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            ocr = raid_ocr(raid=self.config.Campaign_Event, mode=mode)
            remain, _, _ = ocr.ocr(self.device.image)
            logger.attr(f"{mode.capitalize()} Remain", remain)

            # End
            if remain == prev:
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

            prev = remain

        return remain

    def run(self, name=""):
        """
        Args:
            name (str): Raid name, such as 'raid_20200624'
        """
        name = name if name else self.config.Campaign_Event
        stages = [RaidStage(name) for name in STAGES]
        STAGE_FILTER.load(self.config.RaidDaily_StageFilter)
        stages = STAGE_FILTER.apply(stages)

        self.ui_ensure(page_raid)

        for stage in stages:
            mode = stage.name
            logger.hr(mode, level=1)
            for _ in range(15):
                remain = self.get_remain(mode=mode)
                if remain <= 0:
                    break
                super().run(name=name, mode=mode, total=1)

        self.config.task_delay(server_update=True)
