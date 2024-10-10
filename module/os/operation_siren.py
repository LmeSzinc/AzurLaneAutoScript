from datetime import datetime, timedelta

import numpy as np

from module.config.utils import (get_nearest_weekday_date,
                                 get_os_next_reset,
                                 get_os_reset_remain,
                                 get_server_next_update,
                                 DEFAULT_TIME)
from module.exception import RequestHumanTakeover, GameStuckError, ScriptError
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.os.fleet import BossFleet
from module.os.globe_operation import OSExploreError
from module.os.map import OSMap
from module.os_handler.action_point import OCR_OS_ADAPTABILITY, ActionPointLimit
from module.os_handler.assets import OS_MONTHBOSS_NORMAL, OS_MONTHBOSS_HARD, EXCHANGE_CHECK, EXCHANGE_ENTER
from module.os_shop.assets import OS_SHOP_CHECK
from module.shop.shop_voucher import VoucherShop


class OperationSiren(OSMap):
    def os_port_mission(self):
        """
        Visit all ports and do the daily mission in it.
        """
        logger.hr('OS port mission', level=1)
        ports = ['NY City', 'Dakar', 'Taranto', 'Gibraltar', 'Brest', 'Liverpool', 'Kiel', 'St. Petersburg']
        if np.random.uniform() > 0.5:
            ports.reverse()

        for port in ports:
            port = self.name_to_zone(port)
            logger.hr(f'OS port daily in {port}', level=2)
            self.globe_goto(port)

            self.run_auto_search()
            self.handle_after_auto_search()

    def os_finish_daily_mission(self, question=True, rescan=None):
        """
        Finish all daily mission in Operation Siren.
        Suggest to run os_port_daily to accept missions first.

        Args:
            question (bool): refer to run_auto_search
            rescan (None, bool): refer to run_auto_search

        Returns:
            int: Number of missions finished
        """
        logger.hr('OS finish daily mission', level=1)
        count = 0
        while True:
            result = self.os_get_next_mission()
            if not result:
                break

            if result != 'pinned_at_archive_zone':
                # The name of archive zone is "archive zone", which is not an existing zone.
                # After archive zone, it go back to previous zone automatically.
                self.zone_init()
            if result == 'already_at_mission_zone':
                self.globe_goto(self.zone, refresh=True)
            self.fleet_set(self.config.OpsiFleet_Fleet)
            self.os_order_execute(
                recon_scan=False,
                submarine_call=self.config.OpsiFleet_Submarine and result != 'pinned_at_archive_zone')
            self.run_auto_search(question, rescan)
            self.handle_after_auto_search()
            count += 1
            self.config.check_task_switch()

        return count

    def os_daily(self):
        # Finish existing missions first
        # No need anymore, os_mission_overview_accept() is able to handle
        # self.os_finish_daily_mission()

        # Clear tuning samples daily
        if self.config.OpsiDaily_UseTuningSample:
            self.tuning_sample_use()

        while True:
            # If unable to receive more dailies, finish them and try again.
            success = self.os_mission_overview_accept()
            # Re-init zone name
            # MISSION_ENTER appear from the right,
            # need to confirm that the animation has ended,
            # or it will click on MAP_GOTO_GLOBE
            self.zone_init()
            self.os_finish_daily_mission()
            if self.is_in_opsi_explore():
                self.os_port_mission()
                break
            if success:
                break

        self.config.task_delay(server_update=True)

    def os_cross_month_end(self):
        self.config.task_delay(target=get_os_next_reset() - timedelta(minutes=10))
        self.config.task_stop()

    def os_cross_month(self):
        next_reset = get_os_next_reset()
        now = datetime.now()
        logger.attr('OpsiNextReset', next_reset)

        # Check start time
        if next_reset < now:
            raise ScriptError(f'Invalid OpsiNextReset: {next_reset} < {now}')
        if next_reset - now > timedelta(days=3):
            logger.error('Too long to next reset, OpSi might reset already. '
                         'Running OpsiCrossMonth is meaningless, stopped.')
            self.os_cross_month_end()
        if next_reset - now > timedelta(minutes=10):
            logger.error('Too long to next reset, too far from OpSi reset. '
                         'Running OpsiCrossMonth is meaningless, stopped.')
            self.os_cross_month_end()

        # Now we are 10min before OpSi reset
        logger.hr('Wait until OpSi reset', level=1)
        logger.warning('ALAS is now waiting for next OpSi reset, please DO NOT touch the game during wait')
        while True:
            logger.info(f'Wait until {next_reset}')
            now = datetime.now()
            remain = (next_reset - now).total_seconds()
            if remain <= 0:
                break
            else:
                self.device.sleep(min(remain, 60))
                continue

        logger.hr('OpSi reset', level=3)

        def false_func(*args, **kwargs):
            return False

        self.is_in_opsi_explore = false_func
        self.config.task_switched = false_func

        logger.hr('OpSi clear daily', level=1)
        self.config.override(
            OpsiGeneral_DoRandomMapEvent=True,
            OpsiFleet_Fleet=self.config.cross_get('OpsiDaily.OpsiFleet.Fleet'),
            OpsiFleet_Submarine=False,
        )
        count = 0
        empty_trial = 0
        while True:
            # If unable to receive more dailies, finish them and try again.
            success = self.os_mission_overview_accept()
            # Re-init zone name
            # MISSION_ENTER appear from the right,
            # need to confirm that the animation has ended,
            # or it will click on MAP_GOTO_GLOBE
            self.zone_init()
            if empty_trial >= 5:
                logger.warning('No Opsi dailies found within 5 min, stop waiting')
                break
            count += self.os_finish_daily_mission()
            if not count:
                logger.warning('Did not receive any OpSi dailies, '
                               'probably game dailies are not refreshed, wait 1 minute')
                empty_trial += 1
                self.device.sleep(60)
                continue
            if success:
                break

        logger.hr('OS clear abyssal', level=1)
        self.config.override(
            OpsiGeneral_DoRandomMapEvent=False,
            HOMO_EDGE_DETECT=False,
            STORY_OPTION=0,
            OpsiGeneral_UseLogger=True,
            # Obscure
            OpsiObscure_ForceRun=True,
            OpsiFleet_Fleet=self.config.cross_get('OpsiObscure.OpsiFleet.Fleet'),
            OpsiFleet_Submarine=False,
            # Abyssal
            OpsiFleetFilter_Filter=self.config.cross_get('OpsiAbyssal.OpsiFleetFilter.Filter'),
            OpsiAbyssal_ForceRun=True,
        )
        while True:
            if self.storage_get_next_item('ABYSSAL', use_logger=True):
                self.zone_init()
                result = self.run_abyssal()
                if not result:
                    self.map_exit()
                self.fleet_repair(revert=False)
            else:
                break

        logger.hr('OS clear obscure', level=1)
        while True:
            if self.storage_get_next_item('OBSCURE', use_logger=True):
                self.zone_init()
                self.fleet_set(self.config.OpsiFleet_Fleet)
                self.os_order_execute(
                    recon_scan=True,
                    submarine_call=False)
                self.run_auto_search(rescan='current')
                self.map_exit()
                self.handle_after_auto_search()
            else:
                break

        logger.hr(f'OS meowfficer farming, hazard_level=3', level=1)
        self.config.override(
            OpsiGeneral_DoRandomMapEvent=True,
            HOMO_EDGE_DETECT=True,
            STORY_OPTION=-2,
            # Meowfficer farming
            OpsiFleet_Fleet=self.config.cross_get('OpsiMeowfficerFarming.OpsiFleet.Fleet'),
            OpsiFleet_Submarine=False,
            OpsiMeowfficerFarming_ActionPointPreserve=0,
            OpsiMeowfficerFarming_HazardLevel=3,
            OpsiMeowfficerFarming_TargetZone=0,
        )
        while True:
            zones = self.zone_select(hazard_level=3) \
                .delete(SelectedGrids([self.zone])) \
                .delete(SelectedGrids(self.zones.select(is_port=True))) \
                .sort_by_clock_degree(center=(1252, 1012), start=self.zone.location)
            logger.hr(f'OS meowfficer farming, zone_id={zones[0].zone_id}', level=1)
            self.globe_goto(zones[0])
            self.fleet_set(self.config.OpsiFleet_Fleet)
            self.os_order_execute(
                recon_scan=False,
                submarine_call=False)
            self.run_auto_search()
            self.handle_after_auto_search()

    def os_shop(self):
        """
        Buy all supplies in all ports.
        If not having enough yellow coins or purple coins, skip buying supplies in next port.
        """
        logger.hr('OS port daily', level=1)
        if not self.zone.is_azur_port:
            self.globe_goto(self.zone_nearest_azur_port(self.zone))

        self.port_enter()
        self.port_shop_enter()

        if self.appear(OS_SHOP_CHECK):
            not_empty = self.handle_port_supply_buy()
            next_reset = self._os_shop_delay(not_empty)
            logger.info('OS port daily finished, delay to next reset')
            logger.attr('OpsiShopNextReset', next_reset)
        else:
            next_reset = get_os_next_reset()
            logger.warning('There is no shop in the port, skip to the next month.')
            logger.attr('OpsiShopNextReset', next_reset)

        self.port_shop_quit()
        self.port_quit()

        self.config.task_delay(target=next_reset)
        self.config.task_stop()

    def _os_shop_delay(self, not_empty) -> datetime:
        """
        Calculate the delay of OpsiShop.

        Args:
            not_empty (bool): Indicates whether the shop is not empty.

        Returns:
            datetime: The time of the next shop reset.
        """
        next_reset = None

        if not_empty:
            next_reset = get_server_next_update(self.config.Scheduler_ServerUpdate)
        else:
            remain = get_os_reset_remain()
            next_reset = get_os_next_reset()
            if remain == 0:
                next_reset = get_server_next_update(self.config.Scheduler_ServerUpdate)
            elif remain < 7:
                next_reset = next_reset - timedelta(days=1)
            else:
                next_reset = (
                    get_server_next_update(self.config.Scheduler_ServerUpdate) +
                    timedelta(days=6)
                )
        return next_reset

    def _os_voucher_enter(self):
        self.os_map_goto_globe(unpin=False)
        self.ui_click(click_button=EXCHANGE_ENTER, check_button=EXCHANGE_CHECK,
                      offset=(200, 20), retry_wait=3, skip_first_screenshot=True)

    def _os_voucher_exit(self):
        self.ui_back(check_button=EXCHANGE_ENTER, appear_button=EXCHANGE_CHECK,
                     offset=(200, 20), retry_wait=3, skip_first_screenshot=True)
        self.os_globe_goto_map()

    def os_voucher(self):
        logger.hr('OS voucher', level=1)
        self._os_voucher_enter()
        VoucherShop(self.config, self.device).run()
        self._os_voucher_exit()

        next_reset = get_os_next_reset()
        logger.info('OS voucher finished, delay to next reset')
        logger.attr('OpsiNextReset', next_reset)
        self.config.task_delay(target=next_reset)

    def os_meowfficer_farming(self):
        """
        Recommend 3 or 5 for higher meowfficer searching point per action points ratio.
        """
        logger.hr(f'OS meowfficer farming, hazard_level={self.config.OpsiMeowfficerFarming_HazardLevel}', level=1)
        if self.is_cl1_enabled and self.config.OpsiMeowfficerFarming_ActionPointPreserve < 1000:
            logger.info('With CL1 leveling enabled, set action point preserve to 1000')
            self.config.OpsiMeowfficerFarming_ActionPointPreserve = 1000
        preserve = min(self.get_action_point_limit(), self.config.OpsiMeowfficerFarming_ActionPointPreserve, 2000)
        if preserve == 0:
            self.config.override(OpsiFleet_Submarine=False)
        if self.is_cl1_enabled:
            # Without these enabled, CL1 gains 0 profits
            self.config.override(
                OpsiGeneral_DoRandomMapEvent=True,
                OpsiGeneral_AkashiShopFilter='ActionPoint',
                OpsiFleet_Submarine=False,
            )
            cd = self.nearest_task_cooling_down
            logger.attr('Task cooling down', cd)
            # At the last day of every month, OpsiObscure and OpsiAbyssal are scheduled frequently
            # Don't schedule after them
            remain = get_os_reset_remain()
            if cd is not None and remain > 0:
                logger.info(f'Having task cooling down, delay OpsiMeowfficerFarming after it')
                self.config.task_delay(target=cd.next_run)
                self.config.task_stop()
        if self.is_in_opsi_explore():
            logger.warning(f'OpsiExplore is still running, cannot do {self.config.task.command}')
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        ap_checked = False
        while True:
            self.config.OS_ACTION_POINT_PRESERVE = preserve
            if self.config.is_task_enabled('OpsiAshBeacon') \
                    and not self._ash_fully_collected \
                    and self.config.OpsiAshBeacon_EnsureFullyCollected:
                logger.info('Ash beacon not fully collected, ignore action point limit temporarily')
                self.config.OS_ACTION_POINT_PRESERVE = 0
            logger.attr('OS_ACTION_POINT_PRESERVE', self.config.OS_ACTION_POINT_PRESERVE)
            if not ap_checked:
                # Check action points first to avoid using remaining AP when it not enough for tomorrow's daily
                # When not running CL1 and use oil
                keep_current_ap = True
                check_rest_ap = True
                if not self.is_cl1_enabled and self.config.OpsiGeneral_BuyActionPointLimit > 0:
                    keep_current_ap = False
                if self.is_cl1_enabled and self.get_yellow_coins() >= self.config.OS_CL1_YELLOW_COINS_PRESERVE:
                    check_rest_ap = False
                    try:
                        self.action_point_set(cost=0, keep_current_ap=keep_current_ap, check_rest_ap=check_rest_ap)
                    except ActionPointLimit:
                        self.config.task_delay(server_update=True)
                        self.config.task_call('OpsiHazard1Leveling')
                        self.config.task_stop()
                else:
                    self.action_point_set(cost=0, keep_current_ap=keep_current_ap, check_rest_ap=check_rest_ap)
                ap_checked = True

            # (1252, 1012) is the coordinate of zone 134 (the center zone) in os_globe_map.png
            if self.config.OpsiMeowfficerFarming_TargetZone != 0:
                try:
                    zone = self.name_to_zone(self.config.OpsiMeowfficerFarming_TargetZone)
                except ScriptError:
                    logger.warning(f'wrong zone_id input:{self.config.OpsiMeowfficerFarming_TargetZone}')
                    raise RequestHumanTakeover('wrong input, task stopped')
                else:
                    logger.hr(f'OS meowfficer farming, zone_id={zone.zone_id}', level=1)
                    self.globe_goto(zone, refresh=True)
                    self.fleet_set(self.config.OpsiFleet_Fleet)
                    self.os_order_execute(
                        recon_scan=False,
                        submarine_call=self.config.OpsiFleet_Submarine)
                    self.run_auto_search()
                    self.handle_after_auto_search()
                    self.config.check_task_switch()
            else:
                zones = self.zone_select(hazard_level=self.config.OpsiMeowfficerFarming_HazardLevel) \
                    .delete(SelectedGrids([self.zone])) \
                    .delete(SelectedGrids(self.zones.select(is_port=True))) \
                    .sort_by_clock_degree(center=(1252, 1012), start=self.zone.location)

                logger.hr(f'OS meowfficer farming, zone_id={zones[0].zone_id}', level=1)
                self.globe_goto(zones[0])
                self.fleet_set(self.config.OpsiFleet_Fleet)
                self.os_order_execute(
                    recon_scan=False,
                    submarine_call=self.config.OpsiFleet_Submarine)
                self.run_auto_search()
                self.handle_after_auto_search()
                self.config.check_task_switch()

    def os_hazard1_leveling(self):
        logger.hr('OS hazard 1 leveling', level=1)
        # Without these enabled, CL1 gains 0 profits
        self.config.override(
            OpsiGeneral_DoRandomMapEvent=True,
            OpsiGeneral_AkashiShopFilter='ActionPoint',
        )
        if not self.config.is_task_enabled('OpsiMeowfficerFarming'):
            self.config.cross_set(keys='OpsiMeowfficerFarming.Scheduler.Enable', value=True)
        while True:
            # Limited action point preserve of hazard 1 to 200
            self.config.OS_ACTION_POINT_PRESERVE = 200
            if self.config.is_task_enabled('OpsiAshBeacon') \
                    and not self._ash_fully_collected \
                    and self.config.OpsiAshBeacon_EnsureFullyCollected:
                logger.info('Ash beacon not fully collected, ignore action point limit temporarily')
                self.config.OS_ACTION_POINT_PRESERVE = 0
            logger.attr('OS_ACTION_POINT_PRESERVE', self.config.OS_ACTION_POINT_PRESERVE)

            if self.get_yellow_coins() < self.config.OS_CL1_YELLOW_COINS_PRESERVE:
                logger.info(f'Reach the limit of yellow coins, preserve={self.config.OS_CL1_YELLOW_COINS_PRESERVE}')
                with self.config.multi_set():
                    self.config.task_delay(server_update=True)
                    if not self.is_in_opsi_explore():
                        self.config.task_call('OpsiMeowfficerFarming')
                self.config.task_stop()

            self.get_current_zone()

            # Preset action point to 70
            # When running CL1 oil is for running CL1, not meowfficer farming
            keep_current_ap = True
            if self.config.OpsiGeneral_BuyActionPointLimit > 0:
                keep_current_ap = False
            self.action_point_set(cost=70, keep_current_ap=keep_current_ap, check_rest_ap=True)
            if self._action_point_total >= 3000:
                with self.config.multi_set():
                    self.config.task_delay(server_update=True)
                    if not self.is_in_opsi_explore():
                        self.config.task_call('OpsiMeowfficerFarming')
                self.config.task_stop()

            if self.config.OpsiHazard1Leveling_TargetZone != 0:
                zone = self.config.OpsiHazard1Leveling_TargetZone
            else:
                zone = 22
            logger.hr(f'OS hazard 1 leveling, zone_id={zone}', level=1)
            if self.zone.zone_id != zone or not self.is_zone_name_hidden:
                self.globe_goto(self.name_to_zone(zone), types='SAFE', refresh=True)
            self.fleet_set(self.config.OpsiFleet_Fleet)
            self.run_strategic_search()

            self.handle_after_auto_search()
            self.config.check_task_switch()

    def _os_explore_task_delay(self):
        """
        Delay other OpSi tasks during os_explore
        """
        logger.info('Delay other OpSi tasks during OpsiExplore')
        with self.config.multi_set():
            next_run = self.config.Scheduler_NextRun
            for task in ['OpsiObscure', 'OpsiAbyssal', 'OpsiArchive', 'OpsiStronghold', 'OpsiMeowfficerFarming',
                         'OpsiMonthBoss', 'OpsiShop']:
                keys = f'{task}.Scheduler.NextRun'
                current = self.config.cross_get(keys=keys, default=DEFAULT_TIME)
                if current < next_run:
                    logger.info(f'Delay task `{task}` to {next_run}')
                    self.config.cross_set(keys=keys, value=next_run)

    def _os_explore(self):
        """
        Explore all dangerous zones at the beginning of month.
        """

        def end():
            logger.info('OS explore finished, delay to next reset')
            next_reset = get_os_next_reset()
            logger.attr('OpsiNextReset', next_reset)
            logger.info('To run again, clear OpsiExplore.Scheduler.NextRun and set OpsiExplore.OpsiExplore.LastZone=0')
            with self.config.multi_set():
                self.config.OpsiExplore_LastZone = 0
                self.config.OpsiExplore_SpecialRadar = False
                self.config.task_delay(target=next_reset)
                self.config.task_call('OpsiDaily', force_call=False)
                self.config.task_call('OpsiShop', force_call=False)
                self.config.task_call('OpsiHazard1Leveling', force_call=False)
            self.config.task_stop()

        logger.hr('OS explore', level=1)
        order = [int(f.strip(' \t\r\n')) for f in self.config.OS_EXPLORE_FILTER.split('>')]
        # Convert user input
        try:
            last_zone = self.name_to_zone(self.config.OpsiExplore_LastZone).zone_id
        except ScriptError:
            logger.warning(f'Invalid OpsiExplore_LastZone={self.config.OpsiExplore_LastZone}, re-explore')
            last_zone = 0
        # Start from last zone
        if last_zone in order:
            order = order[order.index(last_zone) + 1:]
            logger.info(f'Last zone: {self.name_to_zone(last_zone)}, next zone: {order[:1]}')
        elif last_zone == 0:
            logger.info(f'First run, next zone: {order[:1]}')
        else:
            raise ScriptError(f'Invalid last_zone: {last_zone}')
        if not len(order):
            end()

        # Run
        for zone in order:
            if not self.globe_goto(zone, stop_if_safe=True):
                logger.info(f'Zone cleared: {self.name_to_zone(zone)}')
                self.config.OpsiExplore_LastZone = zone
                continue

            logger.hr(f'OS explore {zone}', level=1)
            if not self.config.OpsiExplore_SpecialRadar:
                # Special radar gives 90 turning samples,
                # If no special radar, use the turning samples in storage to acquire stronger fleets.
                self.tuning_sample_use()
            self.fleet_set(self.config.OpsiFleet_Fleet)
            self.os_order_execute(
                recon_scan=not self.config.OpsiExplore_SpecialRadar,
                submarine_call=self.config.OpsiFleet_Submarine)
            self._os_explore_task_delay()
            self.run_auto_search()
            self.config.OpsiExplore_LastZone = zone
            logger.info(f'Zone cleared: {self.name_to_zone(zone)}')
            self.handle_after_auto_search()
            self.config.check_task_switch()
            if zone == order[-1]:
                end()

    def os_explore(self):
        for _ in range(2):
            try:
                self._os_explore()
            except OSExploreError:
                logger.info('Go back to NY, explore again')
                self.config.OpsiExplore_LastZone = 0
                self.globe_goto(0)

        logger.critical('Failed to solve the locked zone')
        raise GameStuckError

    def clear_obscure(self):
        """
        Raises:
            ActionPointLimit:
        """
        logger.hr('OS clear obscure', level=1)
        self.cl1_ap_preserve()
        if self.config.OpsiObscure_ForceRun:
            logger.info('OS obscure finish is under force run')

        result = self.storage_get_next_item('OBSCURE', use_logger=self.config.OpsiGeneral_UseLogger)
        if not result:
            # No obscure coordinates, delay next run to tomorrow.
            if get_os_reset_remain() > 0:
                self.config.task_delay(server_update=True)
            else:
                logger.info('Just less than 1 day to OpSi reset, delay 2.5 hours')
                self.config.task_delay(minute=150, server_update=True)
            self.config.task_stop()

        self.config.override(
            OpsiGeneral_DoRandomMapEvent=False,
            HOMO_EDGE_DETECT=False,
            STORY_OPTION=0,
        )
        self.zone_init()
        self.fleet_set(self.config.OpsiFleet_Fleet)
        self.os_order_execute(
            recon_scan=True,
            submarine_call=self.config.OpsiFleet_Submarine)
        self.run_auto_search(rescan='current')

        self.map_exit()
        self.handle_after_auto_search()

    def os_obscure(self):
        while True:
            self.clear_obscure()
            if self.config.OpsiObscure_ForceRun:
                self.config.check_task_switch()
                continue
            else:
                break

    def delay_abyssal(self, result=True):
        """
        Args:
            result(bool): If still have obscure coordinates.
        """
        if get_os_reset_remain() == 0:
            logger.info('Just less than 1 day to OpSi reset, delay 2.5 hours')
            self.config.task_delay(minute=150, server_update=True)
            self.config.task_stop()
        elif not result:
            self.config.task_delay(server_update=True)
            self.config.task_stop()

    def clear_abyssal(self):
        """
        Get one abyssal logger in storage,
        attack abyssal boss,
        repair fleets in port.

        Raises:
            ActionPointLimit:
            TaskEnd: If no more abyssal loggers.
            RequestHumanTakeover: If unable to clear boss, fleets exhausted.
        """
        logger.hr('OS clear abyssal', level=1)
        self.cl1_ap_preserve()

        with self.config.temporary(STORY_ALLOW_SKIP=False):
            result = self.storage_get_next_item('ABYSSAL', use_logger=self.config.OpsiGeneral_UseLogger)
        if not result:
            self.delay_abyssal(result=False)

        self.config.override(
            OpsiGeneral_DoRandomMapEvent=False,
            HOMO_EDGE_DETECT=False,
            STORY_OPTION=0
        )
        self.zone_init()
        result = self.run_abyssal()
        if not result:
            raise RequestHumanTakeover

        self.fleet_repair(revert=False)
        self.delay_abyssal()

    def os_abyssal(self):
        while True:
            self.clear_abyssal()
            self.config.check_task_switch()

    def os_archive(self):
        """
        Complete active archive zone in daily mission
        Purchase next available logger archive then repeat
        until exhausted

        Run on weekly basis, AL devs seemingly add new logger
        archives after random scheduled maintenances
        """
        if self.is_in_opsi_explore():
            logger.info('OpsiExplore is under scheduling, stop OpsiArchive')
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        shop = VoucherShop(self.config, self.device)
        while True:
            # In case logger bought manually,
            # finish pre-existing archive zone
            self.os_finish_daily_mission(question=False, rescan=False)

            logger.hr('OS voucher', level=1)
            self._os_voucher_enter()
            bought = shop.run_once()
            self._os_voucher_exit()
            if not bought:
                break

        # Reset to nearest 'Wednesday' date
        next_reset = get_nearest_weekday_date(target=2)
        logger.info('All archive zones finished, delay to next reset')
        logger.attr('OpsiNextReset', next_reset)
        self.config.task_delay(target=next_reset)

    def clear_stronghold(self):
        """
        Find a siren stronghold on globe map,
        clear stronghold,
        repair fleets in port.

        Raises:
            ActionPointLimit:
            TaskEnd: If no more strongholds.
            RequestHumanTakeover: If unable to clear boss, fleets exhausted.
        """
        logger.hr('OS clear stronghold', level=1)
        self.cl1_ap_preserve()

        self.os_map_goto_globe()
        self.globe_update()
        zone = self.find_siren_stronghold()
        if zone is None:
            # No siren stronghold, delay next run to tomorrow.
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        self.globe_enter(zone)
        self.zone_init()
        self.os_order_execute(recon_scan=True, submarine_call=False)
        self.run_stronghold()

        self.fleet_repair(revert=False)
        self.handle_fleet_resolve(revert=False)

    def os_stronghold(self):
        while True:
            self.clear_stronghold()
            self.config.check_task_switch()

    def run_stronghold_one_fleet(self, fleet):
        """
        Args
            fleet (BossFleet):

        Returns:
            bool: If all cleared.
        """
        self.config.override(
            OpsiGeneral_DoRandomMapEvent=False,
            HOMO_EDGE_DETECT=False,
            STORY_OPTION=0
        )
        # Try 3 times, because fleet may stuck in fog.
        for _ in range(3):
            # Attack
            self.fleet_set(fleet.fleet_index)
            self.run_auto_search(question=False, rescan=False)
            self.hp_reset()
            self.hp_get()

            # End
            if self.get_stronghold_percentage() == '0':
                logger.info('BOSS clear')
                return True
            elif any(self.need_repair):
                logger.info('Auto search stopped, because fleet died')
                # Re-enter to reset fleet position
                prev = self.zone
                self.globe_goto(self.zone_nearest_azur_port(self.zone))
                self.handle_fog_block(repair=True)
                self.globe_goto(prev, types='STRONGHOLD')
                return False
            else:
                logger.info('Auto search stopped, because fleet stuck')
                # Re-enter to reset fleet position
                prev = self.zone
                self.globe_goto(self.zone_nearest_azur_port(self.zone))
                self.handle_fog_block(repair=False)
                self.globe_goto(prev, types='STRONGHOLD')
                continue

    def run_stronghold(self):
        """
        All fleets take turns in attacking siren stronghold.

        Returns:
            bool: If success to clear.

        Pages:
            in: Siren logger (abyssal), boss appeared.
            out: If success, dangerous or safe zone.
                If failed, still in abyssal.
        """
        logger.hr(f'Stronghold clear', level=1)
        fleets = self.parse_fleet_filter()
        for fleet in fleets:
            logger.hr(f'Turn: {fleet}', level=2)
            if not isinstance(fleet, BossFleet):
                self.os_order_execute(recon_scan=False, submarine_call=True)
                continue

            result = self.run_stronghold_one_fleet(fleet)
            if result:
                return True
            else:
                continue

        logger.critical('Unable to clear boss, fleets exhausted')
        return False

    def get_adaptability(self):
        adaptability = OCR_OS_ADAPTABILITY.ocr(self.device.image)

        return adaptability

    def clear_month_boss(self):
        """
        check adaptability
        check current boss difficulty
        clear boss
        repair fleets in port

        Raises:
            ActionPointLimit
            TaskEnd: if no more month boss
        """
        if self.is_in_opsi_explore():
            logger.info('OpsiExplore is under scheduling, stop OpsiMonthBoss')
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        logger.hr("OS clear Month Boss", level=1)
        logger.hr("Month Boss precheck", level=2)
        self.os_mission_enter()
        logger.attr('OpsiMonthBoss.Mode', self.config.OpsiMonthBoss_Mode)
        if self.appear(OS_MONTHBOSS_NORMAL, offset=(20, 20)):
            logger.attr('Month boss difficulty', 'normal')
            is_normal = True
        elif self.appear(OS_MONTHBOSS_HARD, offset=(20, 20)):
            logger.attr('Month boss difficulty', 'hard')
            is_normal = False
        else:
            logger.info("No Normal/Hard boss found, stop")
            self.os_mission_quit()
            self.month_boss_delay(is_normal=False, result=False)
            return True
        self.os_mission_quit()

        if not is_normal and self.config.OpsiMonthBoss_Mode == "normal":
            logger.info("Attack normal boss only but having hard boss, skip")
            self.month_boss_delay(is_normal=False, result=True)
            self.config.task_stop()
            return True

        if self.config.OpsiMonthBoss_CheckAdaptability:
            self.os_map_goto_globe(unpin=False)
            adaptability = self.get_adaptability()
            if (np.array(adaptability) < (203, 203, 156)).any():
                logger.info("Adaptability is lower than suppression level, get stronger and come back")
                self.config.task_delay(server_update=True)
                self.config.task_stop()
            # No need to exit, reuse
            # self.os_globe_goto_map()

        # combat
        logger.hr("Month Boss goto", level=2)
        self.globe_goto(154)
        self.go_month_boss_room(is_normal=is_normal)
        result = self.boss_clear(has_fleet_step=True, is_month=True)

        # end
        logger.hr("Month Boss repair", level=2)
        self.fleet_repair(revert=False)
        self.handle_fleet_resolve(revert=False)
        self.month_boss_delay(is_normal=is_normal, result=result)

    def month_boss_delay(self, is_normal=True, result=True):
        """
        Args:
            is_normal: True for normal, False for hard
            result: If success to clear boss
        """
        if is_normal:
            if result:
                if self.config.OpsiMonthBoss_Mode == 'normal_hard':
                    logger.info('Monthly boss normal cleared, run hard boss then')
                    self.config.task_stop()
                else:
                    logger.info('Monthly boss normal cleared, task stop')
                    next_reset = get_os_next_reset()
                    self.config.task_delay(target=next_reset)
                    self.config.task_stop()
            else:
                logger.info("Unable to clear the normal monthly boss, will try later")
                self.config.opsi_task_delay(recon_scan=False, submarine_call=True, ap_limit=False)
                self.config.task_stop()
        else:
            if result:
                logger.info('Monthly boss hard cleared, task stop')
                next_reset = get_os_next_reset()
                self.config.task_delay(target=next_reset)
                self.config.task_stop()
            else:
                logger.info("Unable to clear the hard monthly boss, try again on tomorrow")
                self.config.task_delay(server_update=True)
                self.config.task_stop()


if __name__ == '__main__':
    self = OperationSiren('month_test', task='OpsiMonthBoss')
    from module.os.config import OSConfig

    self.config = self.config.merge(OSConfig())

    self.device.screenshot()
    self.os_init()

    logger.hr("OS clear Month Boss", level=1)
    self.clear_month_boss()
