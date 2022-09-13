import os
import json
from cached_property import cached_property

from alas import AzurLaneAutoScript
from deploy.config import DeployConfig
from module.exception import RequestHumanTakeover
from module.logger import logger

from submodule.AlasMaaBridge.module.config.config import ArknightsConfig
from submodule.AlasMaaBridge.module.handler.handler import AssistantHandler


class FakeDevice:
    @staticmethod
    def empty_func(*args, **kwargs):
        pass

    def __getattr__(self, item):
        return FakeDevice.empty_func


class ArknightsAutoScript(AzurLaneAutoScript):
    @cached_property
    def device(self):
        return FakeDevice()

    @cached_property
    def config(self):
        try:
            config = ArknightsConfig(config_name=self.config_name)
            return config
        except RequestHumanTakeover:
            logger.critical('Request human takeover')
            exit(1)
        except Exception as e:
            logger.exception(e)
            exit(1)

    @staticmethod
    def callback(self):
        pass

    @cached_property
    def asst(self):
        if self.config.task.command not in ['MaaStartup', 'Maa']:
            self.config.task_call('MaaStartup', True)
            self.config.task_stop()

        AssistantHandler.load(self.config.Emulator_MaaPath)

        @AssistantHandler.Asst.CallBackType
        def callback(msg, details, arg):
            """
            Args:
                msg (int):
                details (bytes):
                arg (c_void_p):
            """
            m = AssistantHandler.Message(msg)
            d = details.decode('utf-8', 'ignore')
            logger.info(f'{m} {d}')
            handler = AssistantHandler.ASST_HANDLER
            if handler:
                handler.callback_timer.reset()
                for func in handler.callback_list:
                    func(m, json.loads(d))

        ArknightsAutoScript.callback = callback
        asst = AssistantHandler.Asst(callback)

        if not asst.connect(os.path.abspath(DeployConfig().AdbExecutable), self.config.Emulator_Serial):
            logger.critical('Adb connect failed')
            raise RequestHumanTakeover

        return asst

    def maa_startup(self):
        AssistantHandler(config=self.config, asst=self.asst).startup()

    def maa_annihilation(self):
        AssistantHandler(config=self.config, asst=self.asst).fight()

    def maa_material(self):
        AssistantHandler(config=self.config, asst=self.asst).fight()

    def maa_fight(self):
        AssistantHandler(config=self.config, asst=self.asst).fight()

    def maa_recruit(self):
        AssistantHandler(config=self.config, asst=self.asst).recruit()

    def maa_infrast(self):
        AssistantHandler(config=self.config, asst=self.asst).infrast()

    def maa_visit(self):
        AssistantHandler(config=self.config, asst=self.asst).visit()

    def maa_mall(self):
        AssistantHandler(config=self.config, asst=self.asst).mall()

    def maa_award(self):
        AssistantHandler(config=self.config, asst=self.asst).award()

    def maa_roguelike(self):
        AssistantHandler(config=self.config, asst=self.asst).roguelike()


def loop(config_name):
    ArknightsAutoScript(config_name).loop()


def maa_copilot(config_name):
    script = ArknightsAutoScript(config_name)
    script.config.bind('MaaCopilot')
    AssistantHandler(config=script.config, asst=script.asst).copilot()
