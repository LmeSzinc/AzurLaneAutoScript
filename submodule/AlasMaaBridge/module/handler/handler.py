import os
import sys
import time
from importlib import import_module
from typing import Any

from module.base.timer import Timer
from module.config.utils import read_file, deep_get
from module.exception import RequestHumanTakeover
from module.logger import logger

from submodule.AlasMaaBridge.module.config.config import ArknightsConfig


class AssistantHandler:
    config: ArknightsConfig
    Asst: Any
    Message: Any
    ASST_HANDLER: Any

    @staticmethod
    def load(path):
        sys.path.append(path)
        asst_module = import_module('.asst', 'Python')
        AssistantHandler.Asst = asst_module.Asst
        AssistantHandler.Message = asst_module.Message
        AssistantHandler.Asst.load(path)
        AssistantHandler.ASST_HANDLER = None

    def __init__(self, config, asst, task=None):
        """
        Args:
            config (ArknightsConfig, str): Name of the user config under ./config
            asst (Asst):
            task (str): Bind a task only for dev purpose. Usually to be None for auto task scheduling.
        """
        if isinstance(config, str):
            self.config = ArknightsConfig(config, task=task)
        else:
            self.config = config
        self.interval_timer = {}
        AssistantHandler.ASST_HANDLER = self
        self.asst = asst
        self.callback_timer = Timer(3600)
        self.signal = None
        self.params = None
        self.task_id = None
        self.callback_list = []

    @staticmethod
    def split_filter(string, sep='>'):
        return [f.strip(' \t\r\n') for f in string.split(sep)]

    def maa_start(self, task_name, params):
        self.task_id = self.asst.append_task(task_name, params)
        self.params = params
        self.callback_list.append(self.generic_callback)
        self.callback_timer.reset()
        self.asst.start()
        while 1:
            if self.callback_timer.reached():
                logger.critical('MAA no respond, probably stuck')
                raise RequestHumanTakeover

            if self.signal == self.Message.AllTasksCompleted:
                self.signal = None
                self.task_id = None
                self.callback_list.clear()
                self.asst.stop()
                return

            time.sleep(0.5)

    def generic_callback(self, m, d):
        """
        从MAA的回调中处理任务结束的信息。

        所有其他回调处理函数应遵循同样格式，
        在需要使用的时候加入callback_list，
        可以被随时移除，或在任务结束时自动清空。
        参数的详细说明见https://github.com/MaaAssistantArknights/MaaAssistantArknights/blob/master/docs/3.2-回调信息协议.md

        Args:
            m (Message): 消息类型
            d (dict): 消息详情
        """
        if m == self.Message.AllTasksCompleted:
            self.signal = self.Message.AllTasksCompleted

    def penguin_id_callback(self, m, d):
        if not self.config.MaaRecord_PenguinID \
                and m == self.Message.SubTaskExtraInfo \
                and deep_get(d, keys='what') == 'PenguinId':
            self.config.MaaRecord_PenguinID = deep_get(d, keys='details.id')
            self.params["penguin_id"] = self.config.MaaRecord_PenguinID
            self.asst.set_task_params(self.task_id, self.params)
            self.callback_list.remove(self.penguin_id_callback)

    def annihilation_callback(self, m, d):
        if m == self.Message.SubTaskError:
            self.signal = self.Message.AllTasksCompleted

    def startup(self):
        self.maa_start('StartUp', {
            "client_type": self.config.MaaEmulator_PackageName,
            "start_game_enabled": True
        })
        self.config.task_delay(server_update=True)

    def fight(self):
        args = {
            "stage": self.config.MaaFight_Stage,
            "report_to_penguin": self.config.MaaRecord_ReportToPenguin,
            "server": self.config.MaaEmulator_Server,
            "client_type": self.config.MaaEmulator_PackageName,
            "DrGrandet": self.config.MaaFight_DrGrandet,
        }

        if self.config.MaaFight_Medicine != 0:
            args["medicine"] = self.config.MaaFight_Medicine
        if self.config.MaaFight_Stone != 0:
            args["stone"] = self.config.MaaFight_Stone
        if self.config.MaaFight_Times != 0:
            args["times"] = self.config.MaaFight_Times

        if self.config.MaaFight_Drops:
            old = read_file(os.path.join(self.config.MaaEmulator_MaaPath, './resource/item_index.json'))
            new = {}
            for key, value in old.items():
                new[value['name']] = key
            drops = {}
            drops_filter = self.split_filter(self.config.MaaFight_Drops)
            for drop in drops_filter:
                drop = self.split_filter(drop, sep=':')
                try:
                    drops[new[drop[0]]] = int(drop[1])
                except KeyError:
                    drops[drop[0]] = int(drop[1])
            args['drops'] = drops

        if self.config.MaaRecord_ReportToPenguin and self.config.MaaRecord_PenguinID:
            args["penguin_id"] = self.config.MaaRecord_PenguinID
        elif self.config.MaaRecord_ReportToPenguin and not self.config.MaaRecord_PenguinID:
            self.callback_list.append(self.penguin_id_callback)

        if self.config.task.command == 'MaaAnnihilation':
            self.callback_list.append(self.annihilation_callback)

        self.maa_start('Fight', args)

        if self.config.task.command == 'MaaAnnihilation':
            self.config.task_delay(server_update=True)
        elif self.config.task.command == 'MaaMaterial':
            self.config.Scheduler_Enable = False
        else:
            self.config.task_delay(success=True)

    def recruit(self):
        select = []
        if self.config.MaaRecruit_Select3:
            select.append(3)
        if self.config.MaaRecruit_Select4:
            select.append(4)
        if self.config.MaaRecruit_Select5:
            select.append(5)

        args = {
            "refresh": self.config.MaaRecruit_Refresh,
            "select": select,
            "confirm": select,
            "times": self.config.MaaRecruit_Times,
            "expedite": self.config.MaaRecruit_Expedite,
            "skip_robot": self.config.MaaRecruit_SkipRobot
        }

        if self.config.MaaRecord_ReportToPenguin and self.config.MaaRecord_PenguinID:
            args["penguin_id"] = self.config.MaaRecord_PenguinID
        elif self.config.MaaRecord_ReportToPenguin and not self.config.MaaRecord_PenguinID:
            self.callback_list.append(self.penguin_id_callback)

        self.maa_start('Recruit', args)
        self.config.task_delay(success=True)

    def infrast(self):
        facility = self.split_filter(self.config.MaaInfrast_Facility)
        self.maa_start('Infrast', {
            "facility": facility,
            "drones": self.config.MaaInfrast_Drones,
            "threshold": self.config.MaaInfrast_Threshold
        })
        self.config.task_delay(success=True)

    def visit(self):
        self.maa_start('Visit', {
            "enable": True
        })
        self.config.task_delay(server_update=True)

    def mall(self):
        buy_first = self.split_filter(self.config.MaaMall_BuyFirst)
        blacklist = self.split_filter(self.config.MaaMall_BlackList)
        self.maa_start('Mall', {
            "shopping": self.config.MaaMall_Shopping,
            "buy_first": buy_first,
            "blacklist": blacklist
        })
        self.config.task_delay(server_update=True)

    def award(self):
        self.maa_start('Award', {
            "enable": True
        })
        self.config.task_delay(server_update=True)

    def roguelike(self):
        args = {
            "mode": self.config.MaaRoguelike_Mode,
            "starts_count": self.config.MaaRoguelike_StartsCount,
            "investments_count": self.config.MaaRoguelike_InvestmentsCount,
            "stop_when_investment_full": self.config.MaaRoguelike_StopWhenInvestmentFull,
            "squad": self.config.MaaRoguelike_Squad,
            "roles": self.config.MaaRoguelike_Roles
        }
        if self.config.MaaRoguelike_CoreChar:
            args["core_char"] = self.config.MaaRoguelike_CoreChar

        self.maa_start('Roguelike', args)
        self.config.task_delay(success=True)

    def copilot(self):
        path = self.config.MaaCopilot_FileName
        homework = read_file(path)
        stage = deep_get(homework, keys='stage_name')
        if not stage:
            logger.critical('作业文件不存在或已经损坏')
            raise RequestHumanTakeover

        self.maa_start('Copilot', {
            "stage_name": stage,
            "filename": path,
            "formation": self.config.MaaCopilot_Formation
        })
