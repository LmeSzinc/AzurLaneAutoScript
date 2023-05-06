import json
import os

from cached_property import cached_property

from alas import AzurLaneAutoScript
from module.exception import RequestHumanTakeover
from module.logger import logger
from submodule.AlasFpyBridge.module.config.config import FgoConfig
from submodule.AlasFpyBridge.module.FGOpy import FGOpy


class FgoAutoScript(AzurLaneAutoScript):
    """
    Theoretically, this inheritance from alas is not so necessary
    As long as the configuration file is written in alas's intended format,
    it will work fine in alas's webui

    But when I weighed the options, I decided to stick to AlasMaaBridge :)
    """

    # @override
    device = type("", (), {"__getattr__": lambda *_, **__: lambda *_, **__: None})()

    # @override
    @cached_property
    def config(self):
        try:
            config = FgoConfig(config_name=self.config_name)
            return config
        except RequestHumanTakeover:
            logger.critical("Request human takeover")
            # It'd be better to use sys.exit(1) here because <module 'site'> is not always imported
            # But that's how it's written everywhere else in Alas, so I'll stay consistent
            exit(1)
        except Exception as e:
            logger.exception(e)
            exit(1)

    @cached_property
    def app(self):
        app = FGOpy(self.config.FpyEmulator_Cmdline)
        if not app.run(f"connect {self.config.FpyEmulator_Serial}"):
            logger.critical("Unable to connect to device")
            logger.info("Here are avaliable devices:")
            app.run("connect -l")
            logger.critical("Request human takeover")
            exit(1)
        return app

    def fpy_heartbeat(self):
        assert self.app.run("ping")
        hh, mm = self.config.Interval_Interval.split(":")
        self.config.task_delay(minute=int(hh)*60+int(mm))

    def fpy_main(self):
        assert self.app.run(f"config stopOnDefeated {self.config.Limit_Defeated}")
        assert self.app.run(f"config stopOnKizunaReisou {self.config.Limit_KizunaReisou}")
        assert self.app.run(f"config stopOnSpecialDrop {self.config.Limit_SpecialDrop}")
        assert self.app.run(f"main {self.config.Apple_AppleCount} {self.config.Apple_AppleKind}")
        if self.config.Apple_EatOnce:
            self.config.Apple_AppleCount = 0
        else:
            self.config.Apple_AppleTotal -= self.config.Apple_AppleCount
            self.config.Apple_AppleCount = min(self.config.Apple_AppleCount, self.config.Apple_AppleTotal)
        hh, mm = self.config.Interval_Interval.split(":")
        self.config.task_delay(minute=int(hh)*60+int(mm))
        if self.app.last_error.startswith("Script Stopped"):
            if self.app.last_error == "Script Stopped: Special Drop":
                self.config.Limit_SpecialDrop = 0
            self.config.Scheduler_Enable = False

    def fpy_daily_fp_summon(self):
        assert self.app.run("call dailyFpSummon")
        self.config.task_delay(server_update=True)

    def fpy_battle(self):
        assert self.app.run("battle")
    
    def fpy_benchmark(self):
        for cmd in self.config.Command_Command.splitlines():
            assert self.app.run(cmd)


def loop(config_name):
    FgoAutoScript(config_name).loop()


def set_stop_event(e):
    FgoAutoScript().stop_event = e


def fpy_battle(config_name):
    FgoAutoScript(config_name).fpy_battle()


def fpy_benchmark(config_name):
    script = FgoAutoScript(config_name)
    script.config.bind("FpyBenchmark")
    script.fpy_benchmark()

if __name__ == "__main__":
    fpy_benchmark("fpy")
