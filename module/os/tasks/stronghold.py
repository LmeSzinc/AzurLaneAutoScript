from module.logger import logger
from module.os.fleet import BossFleet
from module.os.map import OSMap


class OpsiStronghold(OSMap):
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
