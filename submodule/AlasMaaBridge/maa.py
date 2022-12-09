import os
import json

from cached_property import cached_property

from alas import AzurLaneAutoScript
from module.exception import RequestHumanTakeover
from module.logger import logger
from submodule.AlasMaaBridge.module.config.config import ArknightsConfig
from submodule.AlasMaaBridge.module.handler.handler import AssistantHandler
from submodule.AlasMaaBridge.module.logger import log_callback


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

        logger.info(f'MAA安装路径：{self.config.MaaEmulator_MaaPath}')
        try:
            incremental_path = None
            if self.config.MaaEmulator_PackageName in ["YoStarEN", "YoStarJP", "YoStarKR", "txwy"]:
                incremental_path = os.path.join(
                    self.config.MaaEmulator_MaaPath,
                    './resource/global/' + self.config.MaaEmulator_PackageName
                )
            AssistantHandler.load(self.config.MaaEmulator_MaaPath, incremental_path)
        except ModuleNotFoundError:
            logger.critical('找不到MAA，请检查安装路径是否正确')
            exit(1)

        @AssistantHandler.Asst.CallBackType
        def callback(msg, details, arg):
            """
            Args:
                msg (int):
                details (bytes):
                arg (c_void_p):
            """
            m = AssistantHandler.Message(msg)
            d = json.loads(details.decode('utf-8', 'ignore'))
            log_callback(m, d)
            handler = AssistantHandler.ASST_HANDLER
            if handler:
                handler.callback_timer.reset()
                for func in handler.callback_list:
                    func(m, d)

        ArknightsAutoScript.callback = callback
        asst = AssistantHandler.Asst(callback)

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


def set_stop_event(e):
    ArknightsAutoScript.stop_event = e


def maa_copilot(config_name):
    script = ArknightsAutoScript(config_name)
    script.config.bind('MaaCopilot')
    handler = AssistantHandler(config=script.config, asst=script.asst)
    handler.connect()
    handler.copilot()
