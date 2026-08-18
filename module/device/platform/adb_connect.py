"""Brute-force adb connect to all discovered emulator instances.

Relocated from deploy.Windows.emulator (removed with the toolkit
installer distribution): the device layer was its last runtime consumer,
and that module lived on the toolkit-bundled DeployConfig chain. This
standalone replacement keeps the same behavior - read AdbExecutable from
config/deploy.yaml, fall back to `adb` on PATH, discover emulator serials
via module.device.platform.emulator_windows, and `adb connect` each.
"""

import asyncio
import os
import subprocess
import sys
from dataclasses import dataclass

from module.base.decorator import cached_property
from module.logger import logger

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


@dataclass
class DataAdbDevice:
    serial: str
    status: str


class AdbConnectManager:
    @cached_property
    def adb(self) -> str:
        from deploy.config import DeployConfig

        exe = DeployConfig().filepath("AdbExecutable")
        if os.path.exists(exe):
            return exe
        logger.warning(f"AdbExecutable: {exe} does not exist, use `adb` instead")
        return "adb"

    @cached_property
    def emulator_manager(self):
        from module.device.platform.emulator_windows import EmulatorManager

        return EmulatorManager()

    @staticmethod
    def subprocess_execute(command: list[str]) -> str:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
        return result.stdout

    def adb_devices(self) -> list[DataAdbDevice]:
        """
        Returns:
            list[DataAdbDevice]: Connected devices in adb
        """
        logger.hr("Adb devices", level=2)
        result = self.subprocess_execute([self.adb, "devices"])
        devices = []
        for line in result.replace("\r\r\n", "\n").replace("\r\n", "\n").split("\n"):
            if line.startswith("List") or "\t" not in line:
                continue
            serial, status = line.split("\t")
            device = DataAdbDevice(
                serial=serial,
                status=status,
            )
            devices.append(device)
            logger.info(device)
        return devices

    def brute_force_connect(self) -> list[DataAdbDevice]:
        """
        Brute-force connect all available emulator instances
        """
        devices = self.adb_devices()

        # Disconnect offline devices
        for device in devices:
            if device.status == "offline":
                self.subprocess_execute([self.adb, "disconnect", device.serial])

        # Get serial
        list_serial = self.emulator_manager.all_emulator_serials

        logger.hr("Brute force connect", level=2)

        async def _connect(serial):
            try:
                await asyncio.create_subprocess_exec(self.adb, "connect", serial)
            except Exception as e:
                logger.info(e)

        async def connect():
            await asyncio.gather(*[_connect(serial) for serial in list_serial])

        asyncio.run(connect())

        return self.adb_devices()
