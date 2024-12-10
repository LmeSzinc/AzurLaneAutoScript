import sys
import typing as t

from pydantic import BaseModel

from module.base.decorator import cached_property, del_cached_property, run_once
from module.device.connection import Connection
from module.device.method.utils import get_serial_pair
from module.device.platform.emulator_base import EmulatorInstanceBase, EmulatorManagerBase, remove_duplicated_path
from module.logger import logger
from module.map.map_grids import SelectedGrids


class EmulatorInfo(BaseModel):
    emulator: str = ''
    name: str = ''
    path: str = ''

    # For APIs of chinac.com, a phone cloud platform.
    # access_key: SecretStr = ''
    # secret: SecretStr = ''


class PlatformBase(Connection, EmulatorManagerBase):
    """
    Base interface of a platform, platform can be various operating system or phone clouds.
    For each `Platform` class, the following APIs must be implemented.
    - all_emulators()
    - all_emulator_instances()
    - switch_window()
    - emulator_check()
    - emulator_start()
    - emulator_stop()
    """

    def switch_window(self, hwnds=None, arg=None):
        """
        Switch emulator's window.
        """
        @run_once
        def skip_switch():
            logger.info(f'Current platform {sys.platform} does not support switch_window, skip')
        skip_switch()
        return True

    def emulator_start(self):
        """
        Start an emulator, until startup completed.
        - Retry is required.
        - Using bored sleep to wait startup is forbidden.
        """
        @run_once
        def skip_start():
            logger.info(f'Current platform {sys.platform} does not support emulator_start, skip')
        skip_start()
        return True

    def emulator_stop(self):
        """
        Stop an emulator.
        """
        @run_once
        def skip_stop():
            logger.info(f'Current platform {sys.platform} does not support emulator_stop, skip')
        skip_stop()
        return True

    def emulator_check(self):
        """
        Check if emulator is running.
        """
        @run_once
        def skip_check():
            logger.info(f'Current platform {sys.platform} does not support emulator_check, skip')
        skip_check()
        return True

    @cached_property
    def emulator_info(self) -> EmulatorInfo:
        emulator = self.config.EmulatorInfo_Emulator
        if emulator == 'auto':
            emulator = ''

        def parse_info(value):
            if isinstance(value, str):
                value = value.strip().replace('\n', '')
                if value in ['None', 'False', 'True']:
                    value = ''
                return value
            else:
                return ''

        name = parse_info(self.config.EmulatorInfo_name)
        path = parse_info(self.config.EmulatorInfo_path)

        return EmulatorInfo(
            emulator=emulator,
            name=name,
            path=path,
        )

    @cached_property
    def emulator_instance(self) -> t.Optional[EmulatorInstanceBase]:
        """
        Returns:
            EmulatorInstanceBase: Emulator instance or None
        """
        data = self.emulator_info
        old_info = dict(
            emulator=data.emulator,
            path=data.path,
            name=data.name,
        )
        # Redirect emulator-5554 to 127.0.0.1:5555
        serial = self.serial
        port_serial, _ = get_serial_pair(self.serial)
        if port_serial is not None:
            serial = port_serial

        instance = self.find_emulator_instance(
            serial=serial,
            name=data.name,
            path=data.path,
            emulator=data.emulator,
        )

        # Write complete emulator data
        if instance is not None:
            new_info = dict(
                emulator=instance.type,
                path=instance.path,
                name=instance.name,
            )
            if new_info != old_info:
                with self.config.multi_set():
                    self.config.EmulatorInfo_Emulator = instance.type
                    self.config.EmulatorInfo_name = instance.name
                    self.config.EmulatorInfo_path = instance.path
                del_cached_property(self, 'emulator_info')

        return instance

    def find_emulator_instance(
            self,
            serial: str,
            name: str = None,
            path: str = None,
            emulator: str = None
    ) -> t.Optional[EmulatorInstanceBase]:
        """
        Args:
            serial: Serial like "127.0.0.1:5555"
            name: Instance name like "Nougat64"
            path: Emulator install path like "C:/Program Files/BlueStacks_nxt/HD-Player.exe"
            emulator: Emulator type defined in Emulator class, like "BlueStacks5"

        Returns:
            EmulatorInstance: Emulator instance or None if no instances not found.
        """
        logger.hr('Find emulator instance', level=2)
        instances = SelectedGrids(self.all_emulator_instances)
        for instance in instances:
            logger.info(instance)
        search_args = dict(serial=serial)

        # Search by serial
        select = instances.select(**search_args)
        if select.count == 0:
            logger.warning(f'No emulator instance with {search_args}, serial invalid')
            return None
        if select.count == 1:
            instance = select[0]
            logger.hr('Emulator instance', level=2)
            logger.info(f'Found emulator instance: {instance}')
            return instance

        # Multiple instances in given serial, search by name
        if name:
            search_args['name'] = name
            select = instances.select(**search_args)
            if select.count == 0:
                logger.warning(f'No emulator instances with {search_args}, name invalid')
                search_args.pop('name')
            elif select.count == 1:
                instance = select[0]
                logger.hr('Emulator instance', level=2)
                logger.info(f'Found emulator instance: {instance}')
                return instance

        # Multiple instances in given serial and name, search by path
        if path:
            search_args['path'] = path
            select = instances.select(**search_args)
            if select.count == 0:
                logger.warning(f'No emulator instances with {search_args}, path invalid')
                search_args.pop('path')
            elif select.count == 1:
                instance = select[0]
                logger.hr('Emulator instance', level=2)
                logger.info(f'Found emulator instance: {instance}')
                return instance

        # Multiple instances in given serial, name and path, search by emulator
        if emulator:
            search_args['type'] = emulator
            select = instances.select(**search_args)
            if select.count == 0:
                logger.warning(f'No emulator instances with {search_args}, type invalid')
                search_args.pop('type')
            elif select.count == 1:
                instance = select[0]
                logger.hr('Emulator instance', level=2)
                logger.info(f'Found emulator instance: {instance}')
                return instance

        # Still too many instances, search from running emulators
        running = remove_duplicated_path(list(self.iter_running_emulator()))
        logger.info('Running emulators')
        for exe in running:
            logger.info(exe)
        if len(running) == 1:
            logger.info('Only one running emulator')
            # Same as searching path
            search_args['path'] = running[0]
            select = instances.select(**search_args)
            if select.count == 0:
                logger.warning(f'No emulator instances with {search_args}, path invalid')
                search_args.pop('path')
            elif select.count == 1:
                instance = select[0]
                logger.hr('Emulator instance', level=2)
                logger.info(f'Found emulator instance: {instance}')
                return instance

        # Still too many instances
        logger.warning(f'Found multiple emulator instances with {search_args}')
        return None
