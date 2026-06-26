import copy
import importlib
import os
import random

from module.campaign.campaign_base import CampaignBase
from module.campaign.campaign_event import CampaignEvent
from module.campaign.campaign_ui import MODE_SWITCH_1
from module.config.config import AzurLaneConfig
from module.exception import CampaignEnd, RequestHumanTakeover, ScriptEnd
from module.handler.fast_forward import map_files, to_map_file_name
from module.logger import logger
from module.notify import handle_notify
from module.ui.page import page_campaign


class CampaignRun(CampaignEvent):
    EMOTION_DOCK_CHECK_TASKS = {'Main', 'Main2', 'Main3', 'Event', 'Event2', 'WarArchives'}
    EMOTION_POPUP_ONLY_STAGE_PREFIX = ('ht', 'c', 'd')

    folder: str
    name: str
    stage: str
    module = None
    config: AzurLaneConfig
    campaign: CampaignBase
    run_count: int
    run_limit: int
    is_stage_loop = False

    def load_campaign(self, name, folder='campaign_main'):
        """
        Args:
            name (str): Name of .py file under module.campaign.
            folder (str): Name of the file folder under campaign.

        Returns:
            bool: If load.
        """
        if hasattr(self, 'name') and name == self.name:
            return False

        self.name = name
        self.folder = folder

        if folder.startswith('campaign_'):
            self.stage = '-'.join(name.split('_')[1:3])
        if folder.startswith('event') or folder.startswith('war_archives'):
            self.stage = name

        try:
            self.module = importlib.import_module('.' + name, f'campaign.{folder}')
        except ModuleNotFoundError:
            logger.warning(f'Map file not found: campaign.{folder}.{name}')
            if not os.path.exists(f'./campaign/{folder}'):
                logger.warning(f'Folder not exists: ./campaign/{folder}')
            else:
                files = map_files(folder)
                logger.warning(f'Existing files: {files}')

            logger.critical(f'Possible reason #1: This event ({folder}) does not have {name}')
            logger.critical(f'Possible reason #2: You are using an old Alas, '
                            'please check for update, or make map files yourself using dev_tools/map_extractor.py')
            raise RequestHumanTakeover

        config = copy.deepcopy(self.config).merge(self.module.Config())
        device = self.device
        self.campaign = self.module.Campaign(config=config, device=device)

        return True

    def triggered_stop_condition(self, oil_check=True):
        """
        Returns:
            bool: If triggered a stop condition.
        """
        # Run count limit
        if self.run_limit and self.config.StopCondition_RunCount <= 0:
            logger.hr('Triggered stop condition: Run count')
            self.config.StopCondition_RunCount = 0
            self.config.Scheduler_Enable = False
            handle_notify(
                self.config.Error_OnePushConfig,
                title=f"Alas <{self.config.config_name}> campaign finished",
                content=f"<{self.config.config_name}> {self.name} reached run count limit"
            )
            return True
        # Lv120 limit
        if self.config.StopCondition_ReachLevel and self.campaign.config.LV_TRIGGERED:
            logger.hr(f'Triggered stop condition: Reach level {self.config.StopCondition_ReachLevel}')
            self.config.Scheduler_Enable = False
            handle_notify(
                self.config.Error_OnePushConfig,
                title=f"Alas <{self.config.config_name}> campaign finished",
                content=f"<{self.config.config_name}> {self.name} reached level limit"
            )
            return True
        # Oil limit
        if oil_check:
            if self.get_oil() < max(500, self.config.StopCondition_OilLimit):
                logger.hr('Triggered stop condition: Oil limit')
                self.config.task_delay(minute=(120, 240))
                return True
        # Auto search oil limit
        if self.campaign.auto_search_oil_limit_triggered:
            logger.hr('Triggered stop condition: Auto search oil limit')
            self.config.task_delay(minute=(120, 240))
            return True
        # If Get a New Ship
        if self.config.StopCondition_GetNewShip and self.campaign.config.GET_SHIP_TRIGGERED:
            logger.hr('Triggered stop condition: Get new ship')
            self.config.Scheduler_Enable = False
            handle_notify(
                self.config.Error_OnePushConfig,
                title=f"Alas <{self.config.config_name}> campaign finished",
                content=f"<{self.config.config_name}> {self.name} got new ship"
            )
            return True
        # Event limit
        if oil_check and self.campaign.event_pt_limit_triggered():
            logger.hr('Triggered stop condition: Event PT limit')
            return True
        # Auto search TaskBalancer
        if self.config.TaskBalancer_Enable and self.campaign.auto_search_coin_limit_triggered:
            logger.hr('Triggered stop condition: Auto search coin limit')
            self.handle_task_balancer()
            return True
        # TaskBalancer
        if oil_check and self.run_count >= 1:
            if self.config.TaskBalancer_Enable and self.triggered_task_balancer():
                logger.hr('Triggered stop condition: Coin limit')
                self.handle_task_balancer()
                return True

        return False

    def _triggered_app_restart(self):
        """
        Returns:
            bool: If triggered a restart condition.
        """
        if not self.campaign.emotion.is_ignore:
            if self.campaign.emotion.triggered_bug():
                logger.info('Triggered restart avoid emotion bug')
                return True

        return False

    def handle_app_restart(self):
        if self._triggered_app_restart():
            self.config.task_call('Restart')
            return True

        return False

    def handle_stage_name(self, name, folder, mode='normal'):
        """
        Handle wrong stage names.
        In some events, the name of SP may be different, such as 'vsp', muse sp.
        To call them easier, their map files should named 'sp.py'.

        Args:
            name (str): Name of .py file.
            folder (str): Name of the file folder under campaign.

        Returns:
            str, str: name, folder
        """
        name = to_map_file_name(name)
        # For GemsFarming, auto choose events or main chapters
        if self.config.task.command == 'GemsFarming':
            if self.stage_is_main(name):
                logger.info(f'Stage name {name} is from campaign_main')
                folder = 'campaign_main'
            else:
                folder = self.config.cross_get('GemsFarming.Campaign.Event')
                if folder is not None:
                    logger.info(f'Stage name {name} is from event {folder}')
                else:
                    logger.warning(f'Cannot get the latest event, fallback to campaign_main')
                    folder = 'campaign_main'
        # Handle special names SP maps
        if folder == 'event_20201126_cn' and name == 'vsp':
            name = 'sp'
        if folder == 'event_20210723_cn' and name == 'vsp':
            name = 'sp'
        if folder == 'event_20220324_cn' and name == 'esp':
            name = 'sp'
        if folder == 'event_20220818_cn' and name == 'esp':
            name = 'sp'
        if folder == 'event_20221124_cn' and name in ['asp', 'a.sp']:
            name = 'sp'
        if folder == 'event_20240425_cn':
            if name in ['μsp', 'usp', 'iisp']:
                name = 'sp'
            name = name.replace('lsp', 'isp').replace('1sp', 'isp')
            if name == 'isp':
                name = 'isp1'
        if folder == 'event_20240724_cn':
            if name in ['ysp', 'y.sp']:
                name = 'sp'
        # Convert to chapter T
        convert = {
            'a1': 't1',
            'a2': 't2',
            'a3': 't3',
            'a4': 't4',
            'a5': 't5',
            'a6': 't6',
            'sp1': 't1',
            'sp2': 't2',
            'sp3': 't3',
            'sp4': 't4',
            'sp5': 't5',
            'sp6': 't6',
        }
        if folder in [
            'event_20211125_cn',
            'event_20231026_cn',
            'event_20241024_cn',
            'event_20250424_cn',
            'event_20250724_cn',
            'event_20250814_cn',
            'event_20251023_cn',
            'event_20260326_cn',
            'event_20260625_cn',
            'war_archives_20230525_cn',
            'war_archives_20231026_cn',
            'war_archives_20240725_cn',
        ]:
            name = convert.get(name, name)
        # Convert between A/B/C/D and T/HT
        convert = {
            'a1': 't1',
            'a2': 't2',
            'a3': 't3',
            'b1': 't4',
            'b2': 't5',
            'b3': 't6',
            'c1': 'ht1',
            'c2': 'ht2',
            'c3': 'ht3',
            'd1': 'ht4',
            'd2': 'ht5',
            'd3': 'ht6',
        }
        if folder in [
            'event_20200917_cn',
            'event_20221124_cn',
            'event_20230525_cn',
            'war_archives_20200917_cn',
            # chapter T
            'event_20211125_cn',
            'event_20231026_cn',
            'event_20231123_cn',
            'event_20240725_cn',
            'event_20240829_cn',
            'event_20241024_cn',
            'event_20241121_cn',
            'event_20250424_cn',
            'event_20250724_cn',
            'event_20250814_cn',
            'event_20251023_cn',
            'event_20260326_cn',
            'event_20260625_cn',
            'war_archives_20230525_cn',
            'war_archives_20231026_cn',
            'war_archives_20240725_cn',
        ]:
            name = convert.get(name, name)
        else:
            reverse = {v: k for k, v in convert.items()}
            name = reverse.get(name, name)
        # The Alchemist and the Archipelago of Secrets
        # Handle typo
        if folder == 'event_20221124_cn':
            name = name.replace('ht', 'th')
        # Chapter TH has no map_percentage and no 3_stars
        if folder == 'event_20221124_cn' and name.startswith('th'):
            if self.config.StopCondition_MapAchievement != 'non_stop':
                logger.info(f'When running chapter TH of event_20221124_cn, '
                            f'StopCondition.MapAchievement is forced set to threat_safe')
                self.config.override(StopCondition_MapAchievement='threat_safe')
        if folder == 'event_20250724_cn' and name.startswith('ts'):
            if self.config.StopCondition_MapAchievement != 'non_stop':
                logger.info(f'When running chapter TS of event_20250724_cn, '
                            f'StopCondition.MapAchievement is forced set to threat_safe')
                self.config.override(StopCondition_MapAchievement='threat_safe')
        # event_20211125_cn, TSS maps are on time maps
        if folder == 'event_20211125_cn' and 'tss' in name:
            self.config.override(
                StopCondition_OilLimit=0,  # No oil cost
                StopCondition_MapAchievement='100_percent_clear',
                StopCondition_StageIncrease=True,
                Emotion_Mode='ignore',  # No emotion cost
                Fleet_Fleet2=0,  # Has only one fleet
                Submarine_Fleet=0,  # No submarine
            )
        # event_20230817_cn story states
        if folder == 'event_20230817_cn':
            if name.startswith('e0'):
                name = 'a1'
        # event_20240829_cn, TP -> SP
        if folder == 'event_20240829_cn':
            if name == 'tp':
                name = 'sp'
        # Stage loop
        for alias, stages in self.config.STAGE_LOOP_ALIAS.items():
            alias_folder, alias = alias
            if folder == alias_folder and name == alias.lower():
                stages = [i.strip(' \t\r\n') for i in stages.split('>')]
                cycle = len(stages)
                count = int(self.config.StopCondition_RunCount)
                if count == 0:
                    stage = random.choice(stages)
                    logger.info(f'Loop stages in {name.upper()}, run random stage: {stage}')
                else:
                    index = count % cycle
                    index = 0 if index == 0 else cycle - index
                    stage = stages[index]
                    logger.info(f'Loop stages in {name.upper()} with remain run_count={count}, '
                                f'run ordered stage: {stage}')
                name = stage.lower()
                self.is_stage_loop = True
                # disable continuous clear
                logger.info('disable continuous clear')
                self.config.override(StopCondition_MapAchievement='non_stop')
                self.config.override(StopCondition_StageIncrease=False)
        # Convert campaign_main to campaign hard if mode is hard and file exists
        if mode == 'hard' and folder == 'campaign_main' and name in map_files('campaign_hard'):
            folder = 'campaign_hard'
        # event_20240912_cn does not have "Threat: Safe" indicator, fallback MapAchievement
        if folder == 'event_20240912_cn':
            if self.config.StopCondition_MapAchievement == 'threat_safe':
                logger.info(
                    'In event_20240912_cn, MapAchievement=threat_safe fallback to map_3_stars')
                self.config.override(StopCondition_MapAchievement='map_3_stars')
            if self.config.StopCondition_MapAchievement == 'threat_safe_without_3_stars':
                logger.info(
                    'In event_20240912_cn, MapAchievement=threat_safe_without_3_stars fallback to 100_percent_clear')
                self.config.override(StopCondition_MapAchievement='100_percent_clear')
        if folder == 'event_20260417_cn':
            if name in ['vsp', ]:
                name = 'sp'
        return name, folder

    def can_use_auto_search_continue(self):
        # Cannot update map info in auto search menu
        # Close it if map achievement is set
        if self.config.StopCondition_MapAchievement != 'non_stop':
            return False

        return self.run_count > 0 and self.campaign.map_is_auto_search

    def handle_commission_notice(self):
        """
        Check commission notice.
        If found, stop current task and call commission.

        Raises:
            TaskEnd: If found commission notice.

        Pages:
            in: page_campaign
        """
        if self.campaign.commission_notice_show_at_campaign():
            logger.info('Commission notice found')
            self.config.task_call('Commission', force_call=True)
            self.config.task_stop('Commission notice found')

    @classmethod
    def is_event_hard_stage(cls, name, folder):
        if not str(folder).startswith('event_'):
            return False
        name = str(name).lower()
        return name.startswith(cls.EMOTION_POPUP_ONLY_STAGE_PREFIX)

    def emotion_popup_only_set(self, name, folder, log=True):
        popup_only = self.is_event_hard_stage(name=name, folder=folder)
        self.config.Emotion_PopupOnly = popup_only
        if hasattr(self, 'campaign'):
            self.campaign.config.Emotion_PopupOnly = popup_only
        if popup_only and log:
            logger.info('Event hard stage uses popup-only emotion control')

    def emotion_dock_calibrate(self):
        """
        Sync current task emotion ledger from normal fleet ships in dock.

        Returns:
            bool: If dock UI might have been entered and campaign UI should be restored.

        Pages:
            in: page_campaign
            out: page_campaign or page_dock
        """
        command = self.config.Scheduler_Command
        if command not in self.EMOTION_DOCK_CHECK_TASKS:
            return False
        if self.campaign.emotion.is_popup_only:
            return False
        if not self.campaign.emotion.is_calculate:
            return False

        fleet_mapping = {}
        for task_fleet in [1, 2]:
            normal_fleet = getattr(self.config, f'Fleet_Fleet{task_fleet}', None)
            try:
                normal_fleet = int(normal_fleet)
            except (TypeError, ValueError):
                logger.warning(f'Invalid Fleet_Fleet{task_fleet}: {normal_fleet}')
                continue
            if 1 <= normal_fleet <= 6:
                fleet_mapping[task_fleet] = normal_fleet
            else:
                logger.warning(f'Invalid Fleet_Fleet{task_fleet}: {normal_fleet}')

        if not fleet_mapping:
            logger.warning('No normal fleet configured for emotion dock calibration')
            return False

        logger.hr('Emotion dock calibration')
        logger.info(f'Task `{command}` fleet mapping: {fleet_mapping}')

        try:
            from module.retire.dock import Dock
            dock = Dock(config=self.config, device=self.device)
            scanned = dock.scan_fleet_emotion(fleet_mapping.values())
        except Exception as e:
            logger.warning(f'Emotion dock calibration failed, keep current ledger: {e}')
            return True

        records = {}
        for task_fleet, normal_fleet in fleet_mapping.items():
            value = scanned.get(normal_fleet)
            if value is None:
                logger.warning(
                    f'No dock emotion result for task fleet {task_fleet} '
                    f'(normal fleet {normal_fleet}), keep current ledger'
                )
                continue
            records[f'Emotion_Fleet{task_fleet}Value'] = value

        if records:
            logger.info(f'Sync emotion ledger from dock: {records}')
            self.config.set_record(**records)
            campaign_records = {}
            for arg in records:
                record = arg.replace('Value', 'Record')
                campaign_records[arg] = getattr(self.config, arg)
                campaign_records[record] = getattr(self.config, record)
            self.campaign.config.override(**campaign_records)
            self.campaign.emotion.update()
            self.campaign.emotion.show()
        else:
            logger.warning('Emotion dock calibration produced no usable records')

        return True

    def emotion_preflight_check(self):
        """
        Delay current task immediately if emotion is below threshold.

        Returns:
            bool: If current task was delayed and should leave the run loop.
        """
        if self.campaign.emotion.is_popup_only:
            return False
        try:
            self.campaign.emotion.check_reduce(self.campaign._map_battle)
        except ScriptEnd as e:
            logger.hr('Script end')
            logger.info(str(e))
            return True
        return False

    def run(self, name, folder='campaign_main', mode='normal', total=0):
        """
        Args:
            name (str): Name of .py file.
            folder (str): Name of the file folder under campaign.
            mode (str): `normal` or `hard`
            total (int):
        """
        name, folder = self.handle_stage_name(name, folder, mode=mode)
        self.config.override(Campaign_Name=name, Campaign_Event=folder)
        self.emotion_popup_only_set(name=name, folder=folder, log=False)
        self.load_campaign(name, folder=folder)
        self.emotion_popup_only_set(name=name, folder=folder)
        self.run_count = 0
        self.run_limit = self.config.StopCondition_RunCount
        emotion_dock_calibration_checked = False
        while 1:
            # End
            if total and self.run_count >= total:
                break
            if self.campaign.event_time_limit_triggered():
                self.config.task_stop()

            # Log
            logger.hr(name, level=1)
            if self.config.StopCondition_RunCount > 0:
                logger.info(f'Count remain: {self.config.StopCondition_RunCount}')
            else:
                logger.info(f'Count: {self.run_count}')

            # UI ensure
            self.device.stuck_record_clear()
            self.device.click_record_clear()
            if not self.device.has_cached_image:
                self.device.screenshot()
            self.campaign.device.image = self.device.image
            if self.campaign.is_in_map():
                logger.info('Already in map, retreating.')
                try:
                    self.campaign.withdraw()
                except CampaignEnd:
                    pass
                self.campaign.ensure_campaign_ui(name=self.stage, mode=mode)
            elif self.campaign.is_in_auto_search_menu():
                if self.can_use_auto_search_continue():
                    logger.info('In auto search menu, skip ensure_campaign_ui.')
                else:
                    logger.info('In auto search menu, closing.')
                    # Because event_20240725 task balancer delete self.campaign.ensure_auto_search_exit()
                    self.campaign.ensure_campaign_ui(name=self.stage, mode=mode)
            else:
                self.campaign.ensure_campaign_ui(name=self.stage, mode=mode)
            self.disable_raid_on_event()
            self.handle_commission_notice()
            if not emotion_dock_calibration_checked:
                emotion_dock_calibration_checked = True
                if self.emotion_dock_calibrate():
                    self.campaign.ensure_campaign_ui(name=self.stage, mode=mode)
                    if self.emotion_preflight_check():
                        break

            # if in hard mode, check remain times
            if self.ui_page_appear(page_campaign) and MODE_SWITCH_1.get(main=self) == 'normal':
                from module.hard.hard import OCR_HARD_REMAIN
                remain = OCR_HARD_REMAIN.ocr(self.device.image)
                if not remain:
                    logger.info('Remaining number of times of hard mode campaign_main is 0, delay task to next day')
                    self.config.task_delay(server_update=True)
                    break

            # End
            if self.triggered_stop_condition(oil_check=not self.campaign.is_in_auto_search_menu()):
                break

            # Run
            self.device.stuck_record_clear()
            self.device.click_record_clear()
            try:
                self.campaign.run()
            except ScriptEnd as e:
                logger.hr('Script end')
                logger.info(str(e))
                break

            # After run
            self.run_count += 1
            if self.config.StopCondition_RunCount:
                self.config.StopCondition_RunCount -= 1
            # End
            if self.triggered_stop_condition(oil_check=False):
                break
            # One-time stage limit
            if self.campaign.config.MAP_IS_ONE_TIME_STAGE:
                if self.run_count >= 1:
                    logger.hr('Triggered one-time stage limit')
                    self.campaign.handle_map_stop()
                    break
            # Loop stages
            if self.is_stage_loop:
                if self.run_count >= 1:
                    logger.hr('Triggered loop stage switch')
                    break
            # Scheduler
            if self.config.task_switched():
                self.campaign.ensure_auto_search_exit()
                self.config.task_stop()

        self.campaign.ensure_auto_search_exit()
