import os
import re
import sys
import json
import time
import requests
import datetime
from importlib import import_module
from typing import Any

from cached_property import cached_property

from deploy.config import DeployConfig
from module.base.timer import Timer
from module.config.utils import read_file, deep_get
from module.device.connection_attr import ConnectionAttr
from module.exception import RequestHumanTakeover
from module.logger import logger

from submodule.AlasMaaBridge.module.config.config import ArknightsConfig


class AssistantHandler:
    config: ArknightsConfig
    Asst: Any
    Message: Any
    ASST_HANDLER: Any

    @staticmethod
    def load(path, incremental_path=None):
        sys.path.append(path)
        try:
            from submodule.AlasMaaBridge.module.handler import asst_backup
            AssistantHandler.Asst = asst_backup.Asst
            AssistantHandler.Message = asst_backup.Message
            AssistantHandler.Asst.load(path, user_dir=path, incremental_path=incremental_path)
        except:
            logger.warning('导入MAA失败，尝试使用原生接口导入')
            asst_module = import_module('.asst', 'Python')
            AssistantHandler.Asst = asst_module.Asst
            AssistantHandler.Message = asst_module.Message
            AssistantHandler.Asst.load(path, user_dir=path, incremental_path=incremental_path)

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

    def maa_stop(self):
        self.asst.stop()
        while 1:
            if self.signal in [
                self.Message.AllTasksCompleted,
                self.Message.TaskChainCompleted,
                self.Message.TaskChainStopped,
                self.Message.TaskChainError
            ]:
                return

    def maa_start(self, task_name, params):
        self.task_id = self.asst.append_task(task_name, params)
        self.signal = None
        self.params = params
        self.callback_list.append(self.task_end_callback)
        self.callback_timer.reset()
        self.asst.start()
        while 1:
            if self.callback_timer.reached():
                logger.critical('MAA no respond, probably stuck')
                raise RequestHumanTakeover

            if self.signal is not None:
                if self.signal == self.Message.TaskChainError:
                    raise RequestHumanTakeover
                self.maa_stop()
                self.callback_list.clear()
                return

            time.sleep(0.5)

    def task_end_callback(self, m, d):
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
        if m in [
            self.Message.AllTasksCompleted,
            self.Message.TaskChainError,
            self.Message.TaskChainStopped
        ]:
            self.signal = m

    def penguin_id_callback(self, m, d):
        if not self.config.MaaRecord_PenguinID \
                and m == self.Message.SubTaskExtraInfo \
                and deep_get(d, keys='what') == 'PenguinId':
            self.config.MaaRecord_PenguinID = deep_get(d, keys='details.id')
            self.callback_list.remove(self.penguin_id_callback)

    def annihilation_callback(self, m, d):
        if m == self.Message.SubTaskError:
            self.signal = m

    def fight_stop_count_callback(self, m, d):
        if m == self.Message.SubTaskCompleted:
            if deep_get(d, keys='details.task') == 'MedicineConfirm' \
                    and self.config.MaaFight_Medicine is not None:
                self.config.MaaFight_Medicine = self.config.MaaFight_Medicine - 1
            elif deep_get(d, keys='details.task') == 'StoneConfirm' \
                    and self.config.MaaFight_Stone is not None:
                self.config.MaaFight_Stone = self.config.MaaFight_Stone - 1

        elif m == self.Message.SubTaskExtraInfo \
                and deep_get(d, keys='what') == 'StageDrops':
            if self.config.MaaFight_Times is not None:
                self.config.MaaFight_Times = self.config.MaaFight_Times - 1

            if self.config.MaaFight_Drops is not None:
                drop_list = deep_get(d, keys='details.drops')
                if drop_list is not None:
                    def replace(matched):
                        value = int(matched.group('value')) - drop['quantity']
                        if value <= 0:
                            raise ValueError
                        return re.sub(r':\d+', f':{value}', matched.group())

                    drops_filter = self.config.MaaFight_Drops
                    try:
                        for drop in drop_list:
                            drops_filter = re.sub(f'{drop["itemId"]}:(?P<value>\\d+)', replace, drops_filter)
                            drops_filter = re.sub(f'{drop["itemName"]}:(?P<value>\\d+)', replace, drops_filter)
                    except ValueError:
                        drops_filter = None
                    self.config.MaaFight_Drops = drops_filter

    def roguelike_callback(self, m, d):
        if self.task_switch_timer.reached():
            if self.config.task_switched():
                self.task_switch_timer = None
                self.params['starts_count'] = 0
                self.asst.set_task_params(self.task_id, self.params)
                self.callback_list.remove(self.roguelike_callback)
            else:
                self.task_switch_timer.reset()

    def serial_check(self):
        """
        serial check
        """
        if self.is_bluestacks4_hyperv:
            self.serial = ConnectionAttr.find_bluestacks4_hyperv(self.serial)
        if self.is_bluestacks5_hyperv:
            self.serial = ConnectionAttr.find_bluestacks5_hyperv(self.serial)

    @cached_property
    def is_bluestacks4_hyperv(self):
        return "bluestacks4-hyperv" in self.serial

    @cached_property
    def is_bluestacks5_hyperv(self):
        return "bluestacks5-hyperv" in self.serial

    def connect(self):
        adb = os.path.abspath(DeployConfig().AdbExecutable)
        self.serial = self.config.MaaEmulator_Serial
        self.serial_check()

        old_callback_list = self.callback_list
        self.callback_list = []

        if not self.asst.connect(adb, self.serial):
            raise RequestHumanTakeover

        self.callback_list = old_callback_list

    def startup(self):
        self.connect()
        self.maa_start('StartUp', {
            "client_type": self.config.MaaEmulator_PackageName,
            "start_game_enabled": True
        })
        self.config.task_delay(server_update=True)

    def fight(self):
        args = {
            "report_to_penguin": self.config.MaaRecord_ReportToPenguin,
            "client_type": self.config.MaaEmulator_PackageName,
            "DrGrandet": self.config.MaaFight_DrGrandet,
        }
        if self.config.MaaFight_Stage == 'last':
            args['stage'] = ''
        elif self.config.MaaFight_Stage == 'custom':
            args['stage'] = self.config.MaaFight_CustomStage
        else:
            args['stage'] = self.config.MaaFight_Stage

        if self.config.MaaFight_Medicine is not None:
            args["medicine"] = self.config.MaaFight_Medicine
        if self.config.MaaFight_RunOutOfMedicine:
            args["medicine"] = 999
        if self.config.MaaFight_Stone is not None:
            args["stone"] = self.config.MaaFight_Stone
        if self.config.MaaFight_Times is not None:
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

        if self.config.task.command == 'MaaMaterial':
            self.callback_list.append(self.fight_stop_count_callback)
        if self.config.task.command == 'MaaAnnihilation':
            self.callback_list.append(self.annihilation_callback)

        self.maa_start('Fight', args)

        if self.config.task.command == 'MaaAnnihilation':
            self.config.task_delay(server_update=True)
        elif self.config.task.command == 'MaaMaterial':
            if self.signal == self.Message.AllTasksCompleted:
                with self.config.multi_set():
                    self.config.MaaFight_Medicine = None
                    self.config.MaaFight_Stone = None
                    self.config.MaaFight_Times = None
                    self.config.MaaFight_Drops = None
                    self.config.Scheduler_Enable = False
            else:
                self.config.task_delay(success=False)
        else:
            self.config.task_delay(success=True)

    def recruit(self):
        confirm = []
        if self.config.MaaRecruit_Select3:
            confirm.append(3)
        if self.config.MaaRecruit_Select4:
            confirm.append(4)
        if self.config.MaaRecruit_Select5:
            confirm.append(5)

        args = {
            "refresh": self.config.MaaRecruit_Refresh,
            "select": [4, 5, 6],
            "confirm": confirm,
            "times": self.config.MaaRecruit_Times,
            "expedite": self.config.MaaRecruit_Expedite,
            "skip_robot": self.config.MaaRecruit_SkipRobot
        }

        if self.config.MaaRecruit_Level3ShortTime:
            args['recruitment_time'] = {'3': 460}

        if self.config.MaaRecord_ReportToPenguin and self.config.MaaRecord_PenguinID:
            args["penguin_id"] = self.config.MaaRecord_PenguinID
        elif self.config.MaaRecord_ReportToPenguin and not self.config.MaaRecord_PenguinID:
            self.callback_list.append(self.penguin_id_callback)

        self.maa_start('Recruit', args)
        self.config.task_delay(success=True)

    def infrast(self):
        args = {
            "facility": self.split_filter(self.config.MaaInfrast_Facility),
            "drones": self.config.MaaInfrast_Drones,
            "threshold": self.config.MaaInfrast_Threshold,
            "replenish": self.config.MaaInfrast_Replenish,
            "dorm_notstationed_enabled": self.config.MaaInfrast_Notstationed,
            "drom_trust_enabled": self.config.MaaInfrast_Trust
        }

        end_time = datetime.datetime.now() + datetime.timedelta(minutes=30)
        if self.config.MaaCustomInfrast_Enable:
            args['mode'] = 10000
            args['filename'] = self.config.MaaCustomInfrast_Filename
            plans = deep_get(read_file(self.config.MaaCustomInfrast_Filename), keys='plans')
            for i in range(len(plans)):
                periods = deep_get(plans[i], keys='period')
                if periods is None:
                    logger.critical('无法找到配置文件中的排班周期，请检查文件是否有效')
                    raise RequestHumanTakeover
                for j, period in enumerate(periods):
                    start_time = datetime.datetime.combine(
                        datetime.date.today(),
                        datetime.datetime.strptime(period[0], '%H:%M').time()
                    )
                    end_time = datetime.datetime.combine(
                        datetime.date.today(),
                        datetime.datetime.strptime(period[1], '%H:%M').time()
                    )
                    now_time = datetime.datetime.now()
                    if start_time <= now_time <= end_time:
                        args['plan_index'] = i
                        # 处理跨天的情形
                        # 如："period": [["22:00", "23:59"], ["00:00","06:00"]]
                        if j != len(periods) - 1 and period[1] == '23:59' and periods[j + 1][0] == '00:00':
                            end_time = datetime.datetime.combine(
                                datetime.date.today() + datetime.timedelta(days=1),
                                datetime.datetime.strptime(periods[j + 1][1], '%H:%M').time()
                            )
                        break
                if 'plan_index' in args:
                    break

        self.maa_start('Infrast', args)
        if self.config.MaaCustomInfrast_Enable:
            self.config.task_delay(target=end_time + datetime.timedelta(minutes=1))
        else:
            # 根据心情阈值计算下次换班时间
            # 心情阈值 * 24 / 0.75 * 60
            self.config.task_delay(minute=self.config.MaaInfrast_Threshold * 1920)

    def visit(self):
        self.maa_start('Visit', {
            "enable": True
        })
        self.config.task_delay(server_update=True)

    def mall(self):
        buy_first = self.split_filter(self.config.MaaMall_BuyFirst)
        blacklist = self.split_filter(self.config.MaaMall_BlackList)
        credit_fight = self.config.MaaMall_CreditFight
        if self.config.cross_get(keys='MaaMaterial.MaaFight.Stage') == 'last' \
                and self.config.cross_get(keys='MaaMaterial.Scheduler.Enable', default=False):
            credit_fight = False
        if self.config.cross_get(keys='MaaFight.MaaFight.Stage') == 'last' \
                and self.config.cross_get(keys='MaaFight.Scheduler.Enable', default=False):
            credit_fight = False
        self.maa_start('Mall', {
            "credit_fight": credit_fight,
            "shopping": self.config.MaaMall_Shopping,
            "buy_first": buy_first,
            "blacklist": blacklist,
            "force_shopping_if_credit_full": self.config.MaaMall_ForceShoppingIfCreditFull
        })
        self.config.task_delay(server_update=True)

    def award(self):
        self.maa_start('Award', {
            "enable": True
        })
        self.config.task_delay(server_update=True)

    def roguelike(self):
        args = {
            "theme": self.config.MaaRoguelike_Theme,
            "mode": self.config.MaaRoguelike_Mode,
            "starts_count": self.config.MaaRoguelike_StartsCount,
            "investments_count": self.config.MaaRoguelike_InvestmentsCount,
            "stop_when_investment_full": self.config.MaaRoguelike_StopWhenInvestmentFull,
            "squad": self.config.MaaRoguelike_Squad,
            "roles": self.config.MaaRoguelike_Roles
        }
        if self.config.MaaRoguelike_CoreChar:
            args["core_char"] = self.config.MaaRoguelike_CoreChar

        self.task_switch_timer = Timer(30).start()
        self.callback_list.append(self.roguelike_callback)
        self.maa_start('Roguelike', args)

        if self.task_switch_timer is not None:
            self.config.Scheduler_Enable = False

    def copilot(self):
        filename = self.config.MaaCopilot_FileName
        if filename.startswith('maa://'):
            logger.info('正在从神秘代码中下载作业')
            r = requests.get(f"https://api.prts.plus/copilot/get/{filename.strip('maa://')}", timeout=30)
            if r.status_code != 200:
                logger.critical('作业文件下载失败，请检查神秘代码或网络状况')
                raise RequestHumanTakeover
            logger.info('作业下载完毕')

            r.encoding = 'utf-8'
            buf = json.loads(r.text)['data']['content'].encode('utf-8')
            filename = os.path.join(self.config.MaaEmulator_MaaPath, './resource/_temp_copilot.json')
            filename = filename.replace('\\', '/').replace('./', '/').replace('//', '/')
            with open(filename, 'wb') as f:
                f.write(buf)

        homework = read_file(filename)
        stage = deep_get(homework, keys='stage_name')
        if not stage:
            logger.critical('作业文件不存在或已经损坏')
            raise RequestHumanTakeover

        self.maa_start('Copilot', {
            "stage_name": stage,
            "filename": filename,
            "formation": self.config.MaaCopilot_Formation
        })
