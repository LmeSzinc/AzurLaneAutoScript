import copy
import os
import random

from module.campaign.campaign_base import CampaignBase
from module.campaign.campaign_event import CampaignEvent
from module.campaign.campaign_ui import MODE_SWITCH_1
from module.campaign.map_loader import load_logic, load_map
from module.campaign.stage_meta import CHAPTER_CONVERT_REVERSE, load_stage_meta
from module.config.config import AzurLaneConfig
from module.exception import CampaignEnd, RequestHumanTakeover, ScriptEnd
from module.handler.fast_forward import map_files, to_map_file_name
from module.logger import logger
from module.notify import handle_notify
from module.ui.page import page_campaign


class CampaignRun(CampaignEvent):
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
        Load a map module (MAP / Config / Campaign).

        Args:
            name (str): Name of .py file under module.campaign.
            folder (str): Name of the file folder under campaign.

        Returns:
            bool: If load.
        """
        return self._load_module(load_map, name, folder)

    def load_campaign_logic(self, name, folder):
        """
        Load a logic module (Config / Campaign only, no MAP of its own), e.g.
        the campaign_hard mother module. The caller injects the stage map
        afterwards (hard.py loads it from campaign_main).

        Args:
            name (str): Name of .py file under module.campaign.
            folder (str): Name of the file folder under campaign.

        Returns:
            bool: If load.
        """
        return self._load_module(load_logic, name, folder)

    def _load_module(self, loader, name, folder):
        """
        Shared load path: resolve the module through a role-aware loader
        (`load_map` for map modules, `load_logic` for logic modules), then
        build the config merge and the campaign instance.

        Args:
            loader: callable(folder, name) -> LoadedMap | LoadedLogic.
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
            # Phase 4A: JSON data first, legacy .py fallback (map_loader).
            self.module = loader(folder, name)
        except ModuleNotFoundError:
            logger.warning(f'Map file not found: campaign.{folder}.{name}')
            if not os.path.exists(f'./campaign/{folder}'):
                logger.warning(f'Folder not exists: ./campaign/{folder}')
            else:
                files = map_files(folder)
                logger.warning(f'Existing files: {files}')

            logger.critical(f'Possible reason #1: This event ({folder}) does not have {name}')
            logger.critical('Possible reason #2: You are using an old Alas, '
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


    def handle_stage_name(self, name, folder, mode='normal'):
        """
        Handle wrong stage names.

        Phase 456 D1: per-event normalization moved to campaign/<folder>/meta.json
        (see module/campaign/stage_meta.py). Rule order mirrors the legacy
        if-chain; equivalence is gated by dev_tools/verify_stage_meta.py.
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
                    logger.warning('Cannot get the latest event, fallback to campaign_main')
                    folder = 'campaign_main'

        meta = load_stage_meta(folder)
        rules = list(meta.get('rules', []))
        if not any(rule['type'] == 'chapter_convert' for rule in rules):
            # Legacy else-branch: folders outside the whitelist get the reverse
            # mapping, applied right after the alias stage.
            index = 0
            while index < len(rules) and rules[index]['type'] in ('alias', 'alias_startswith'):
                index += 1
            rules.insert(index, {'type': 'chapter_convert_reverse'})
        for rule in rules:
            typ = rule['type']
            if typ == 'alias' and name in rule['map']:
                name = rule['map'][name]
            elif typ == 'alias_startswith':
                for prefix, value in rule['map'].items():
                    if name.startswith(prefix):
                        name = value
                        break
            elif typ == 'chapter_convert':
                name = rule['map'].get(name, name)
            elif typ == 'chapter_convert_reverse':
                name = CHAPTER_CONVERT_REVERSE.get(name, name)
            elif typ == 'replace_prefix':
                for old, new in rule['map'].items():
                    name = name.replace(old, new)
            elif typ == 'override' and self._override_condition(rule, name):
                for key, value in rule['config'].items():
                    self.config.override(**{key: value})

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
        return name, folder

    def _override_condition(self, rule, name):
        """Phase 456 D1: condition helpers for override rules (default: always)."""
        if 'when_name_startswith' in rule:
            return name.startswith(rule['when_name_startswith'])
        if 'when_name_contains' in rule:
            return rule['when_name_contains'] in name
        if 'when_attr' in rule:
            return getattr(self.config, rule['when_attr']) == rule['when_value']
        return True

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
        self.load_campaign(name, folder=folder)
        self.run_count = 0
        self.run_limit = self.config.StopCondition_RunCount
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
            self.config.override(Campaign_Mode=self.campaign.config.Campaign_Mode)
            self.disable_raid_on_event()
            self.handle_commission_notice()

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
