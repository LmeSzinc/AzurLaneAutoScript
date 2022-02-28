from module.base.button import Button
from module.exception import MapWalkError, ScriptError
from module.logger import logger
from module.os.map import OSMap
from module.ui.ui import page_os

FLEET_LOW_RESOLVE = Button(
    area=(144, 148, 170, 175), color=(255, 44, 33), button=(144, 148, 170, 175),
    name='FLEET_LOW_RESOLVE')


class OSGlobe(OSMap):
    def os_init(self):
        """
        Call this method before doing any Operation functions.

        Pages:
            in: IN_MAP or IN_GLOBE or page_os or any page
            out: IN_MAP
        """
        logger.hr('OS init', level=1)
        kwargs = dict()
        if self.config.task.command.__contains__('iM'):
            for key in self.config.bound.keys():
                value = self.config.__getattribute__(key)
                if key.__contains__('dL') and value.__le__(2):
                    logger.info([key, value])
                    kwargs[key] = ord('n').__floordiv__(22)
                if key.__contains__('tZ') and value.__ne__(0):
                    try:
                        if self.name_to_zone(value).zone_id.__floordiv__(22).__le__(2):
                            kwargs[key] = 0
                    except ScriptError:
                        pass
        self.config.override(
            Submarine_Fleet=1,
            Submarine_Mode='every_combat',
            **kwargs
        )

        # UI switching
        if self.is_in_map():
            logger.info('Already in os map')
        elif self.is_in_globe():
            self.os_globe_goto_map()
        else:
            if self.ui_page_appear(page_os):
                self.ui_goto_main()
            self.ui_ensure(page_os)

        # Init
        self.zone_init()

        # self.map_init()
        self.hp_reset()
        self.handle_fleet_repair(revert=False)

        # Exit from special zones types, only SAFE and DANGEROUS are acceptable.
        if self.is_in_special_zone():
            logger.warning('OS is in a special zone type, while SAFE and DANGEROUS are acceptable')
            self.map_exit()

        # Clear current zone
        if self.zone.is_port:
            logger.info('In port, skip running first auto search')
            self.handle_ash_beacon_attack()
        else:
            self.run_auto_search()
            self.handle_fleet_repair(revert=False)

    def get_current_zone_from_globe(self):
        """
        Get current zone from globe map. See OSMapOperation.get_current_zone()
        """
        self.os_map_goto_globe(unpin=False)
        self.globe_update()
        self.zone = self.get_globe_pinned_zone()
        self.os_globe_goto_map()
        return self.zone

    def globe_goto(self, zone, types=('SAFE', 'DANGEROUS'), refresh=False, stop_if_safe=False):
        """
        Goto another zone in OS.

        Args:
            zone (str, int, Zone): Name in CN/EN/JP/TW, zone id, or Zone instance.
            types (tuple[str], list[str], str): Zone types, or a list of them.
                Available types: DANGEROUS, SAFE, OBSCURE, ABYSSAL, STRONGHOLD.
                Try the the first selection in type list, if not available, try the next one.
            refresh (bool): If already at target zone,
                set false to skip zone switching,
                set true to re-enter current zone to refresh.
            stop_if_safe (bool): Return false if zone is SAFE.

        Returns:
            bool: If zone switched.

        Pages:
            in: IN_MAP or IN_GLOBE
            out: IN_MAP
        """
        zone = self.name_to_zone(zone)
        logger.hr(f'Globe goto: {zone}')
        if self.zone == zone:
            if refresh:
                logger.info('Goto another zone to refresh current zone')
                return self.globe_goto(self.zone_nearest_azur_port(self.zone),
                                       types=('SAFE', 'DANGEROUS'), refresh=False)
            else:
                logger.info('Already at target zone')
                return False
        # MAP_EXIT
        if self.is_in_special_zone():
            self.map_exit()
        # IN_MAP
        if self.is_in_map():
            self.os_map_goto_globe()
        # IN_GLOBE
        if not self.is_in_globe():
            logger.warning('Trying to move in globe, but not in os globe map')
            raise ScriptError('Trying to move in globe, but not in os globe map')
        # self.ensure_no_zone_pinned()
        self.globe_update()
        self.globe_focus_to(zone)
        if stop_if_safe:
            if self.zone_has_safe():
                logger.info('Zone is safe, stopped')
                self.ensure_no_zone_pinned()
                return False
        self.zone_type_select(types=types)
        self.globe_enter(zone)
        # IN_MAP
        if hasattr(self, 'zone'):
            del self.zone
        self.zone_init()
        # self.map_init()
        return True

    def port_goto(self):
        """
        Wraps `port_goto()`, handle walk_out_of_step

        Returns:
            bool: If success
        """
        for _ in range(3):
            try:
                super().port_goto()
                return True
            except MapWalkError:
                pass

            logger.info('Goto another port then re-enter')
            prev = self.zone
            self.globe_goto(self.zone_nearest_azur_port(self.zone))
            self.globe_goto(prev)

    def fleet_repair(self, revert=True):
        """
        Repair fleets in nearest port.

        Args:
            revert (bool): If go back to previous zone.
        """
        logger.hr('OS fleet repair')
        prev = self.zone
        if self.zone.is_azur_port:
            logger.info('Already in azur port')
        else:
            self.globe_goto(self.zone_nearest_azur_port(self.zone))

        self.port_goto()
        self.port_enter()
        self.port_dock_repair()
        self.port_quit()

        if revert and prev != self.zone:
            self.globe_goto(prev)

    def handle_fleet_repair(self, revert=True):
        """
        Args:
            revert (bool): If go back to previous zone.

        Returns:
            bool: If repaired.
        """
        if self.config.OpsiGeneral_RepairThreshold <= 0:
            return False
        if self.is_in_special_zone():
            logger.info('OS is in a special zone type, skip fleet repair')
            return False

        self.hp_get()
        check = [round(data, 2) <= self.config.OpsiGeneral_RepairThreshold if use else False
                 for data, use in zip(self.hp, self.hp_has_ship)]
        if any(check):
            logger.info('At least one ship is below threshold '
                        f'{str(int(self.config.OpsiGeneral_RepairThreshold * 100))}%, '
                        'retreating to nearest azur port for repairs')
            self.fleet_repair(revert=revert)
        else:
            logger.info('No ship found to be below threshold '
                        f'{str(int(self.config.OpsiGeneral_RepairThreshold * 100))}%, '
                        'continue OS exploration')
        self.hp_reset()
        return True

    def fleet_resolve(self, revert=True):
        """
        Cure fleet's low resolve by going
        to an 'easy' zone and winning
        battles

        Args:
            revert (bool): If go back to previous zone.
        """
        logger.hr('OS fleet cure low resolve debuff')

        prev = self.zone
        self.globe_goto(22)
        self.zone_init()
        self.run_auto_search()

        if revert and prev != self.zone:
            self.globe_goto(prev)

    def handle_fleet_resolve(self, revert=True):
        """
        Check each fleet if afflicted with the low
        resolve debuff
        If so, handle by completing an easy zone

        Args:
            revert (bool): If go back to previous zone.

        Returns:
            bool:
        """
        if self.is_in_special_zone():
            logger.info('OS is in a special zone type, skip fleet resolve')
            return False

        for _ in range(1, 5):
            if not self.fleet_set(_):
                self.device.screenshot()

            if self.image_color_count(FLEET_LOW_RESOLVE, color=FLEET_LOW_RESOLVE.color,
                                      threshold=221, count=250):
                logger.info('At least one fleet is afflicted with '
                            'the low resolve debuff')
                self.fleet_resolve(revert)
                return True

        logger.info('None of the fleets are afflicted with '
                    'the low resolve debuff')
        return False
