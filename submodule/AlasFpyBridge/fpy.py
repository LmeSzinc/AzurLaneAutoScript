import json
import os
from functools import wraps

import inflection
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
        app = FGOpy(
            self.config.FpyEmulator_LaunchPath,
            {
                "Special Drop": lambda:
                    setattr(self.config, "FpyLimit_SpecialDrop", max(0, getattr(self.config, "FpyLimit_SpecialDrop") - 1)),
            },
        )
        assert app.run("ping")
        if not app.run(f"connect {self.config.FpyEmulator_Serial}"):
            logger.critical("Unable to connect to device")
            logger.info("Here are avaliable devices:")
            app.run("connect -l")
            logger.critical("Request human takeover")
            exit(1)
        return app

    def fpy_heartbeat(self):
        assert self.app.run("ping")
        hh, mm = self.config.FpyInterval_Interval.split(":")
        self.config.task_delay(minute=int(hh) * 60 + int(mm))

    def fpy_main(self):
        assert self.app.run(f"config stopOnDefeated {self.config.FpyLimit_Defeated}")
        assert self.app.run(f"config stopOnKizunaReisou {self.config.FpyLimit_KizunaReisou}")
        assert self.app.run(f"config stopOnSpecialDrop {self.config.FpyLimit_SpecialDrop}")
        assert self.app.run(f"teamup set index {self.config.FpyTeam_Index}")
        assert self.app.run(f"main {self.config.FpyApple_AppleCount} {self.config.FpyApple_AppleKind}")
        with self.config.multi_set():
            if self.app.last_error.startswith("Script Stopped"):
                self.config.Scheduler_Enable = False
                return
            if self.config.FpyApple_EatOnce:
                self.config.FpyApple_AppleCount = 0
            else:
                self.config.FpyApple_AppleTotal -= self.config.FpyApple_AppleCount
                self.config.FpyApple_AppleCount = min(
                    self.config.FpyApple_AppleCount,
                    self.config.FpyApple_AppleTotal,
                )
            hh, mm = self.config.FpyInterval_Interval.split(":")
            self.config.task_delay(minute=int(hh) * 60 + int(mm))

    def fpy_daily_fp_summon(self):
        assert self.app.run("call dailyFpSummon")
        self.config.task_delay(server_update=True)

    def fpy_battle(self):
        assert self.app.run("battle")

    def fpy_benchmark(self):
        assert self.app.run(f"bench {dict([('touch','-i'),('screen','-o'),('all','')])[self.config.FpyBenchmark_BenchOption]}")

    def fpy_call(self):
        assert self.app.run(f"call {self.config.FpyCall_Function}")


def loop(config_name):
    FgoAutoScript(config_name).loop()


def set_stop_event(e):
    FgoAutoScript.stop_event = e


def export_method(func):
    @wraps(func)
    def wrapper(config_name):
        script = FgoAutoScript(config_name)
        script.config.bind(inflection.camelize(func.__name__))
        getattr(script, func.__name__)()
        script.app.pipe.stdin.close()
        script.app.logger.join(10)

    return wrapper


@export_method
def fpy_battle(config_name):
    pass


@export_method
def fpy_benchmark(config_name):
    pass


@export_method
def fpy_call(config_name):
    pass
