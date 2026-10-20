import os
import re
import subprocess
import typing as t

from module.device.platform.emulator_base import EmulatorBase, EmulatorInstanceBase, EmulatorManagerBase
from module.device.platform.utils import cached_property

BLUESTACKS_BUNDLE_ID = 'com.now.gg.BlueStacks'
BLUESTACKS_EXE = 'Contents/MacOS/BlueStacks'
BLUESTACKS_CONFIG = '/Users/Shared/Library/Application Support/BlueStacks/bluestacks.conf'


class EmulatorInstance(EmulatorInstanceBase):
    @cached_property
    def emulator(self):
        """
        Returns:
            Emulator:
        """
        return Emulator(self.path)


class Emulator(EmulatorBase):
    @classmethod
    def path_to_type(cls, path: str) -> str:
        """
        Args:
            path: Path to emulator executable

        Returns:
            str: Emulator type, such as Emulator.BlueStacks5
        """
        if path.endswith(f'/BlueStacks.app/{BLUESTACKS_EXE}'):
            return cls.BlueStacks5

        return ''

    def iter_instances(self):
        """
        Yields:
            EmulatorInstance: Emulator instances found in this emulator
        """
        if self == Emulator.BlueStacks5:
            try:
                with open(BLUESTACKS_CONFIG, encoding='utf-8') as f:
                    content = f.read()
            except FileNotFoundError:
                return
            # bst.instance.Tiramisu64.status.adb_port="5555"
            emulators = re.findall(r'bst.instance.(\w+).status.adb_port="(\d+)"', content)
            for emulator in emulators:
                yield EmulatorInstance(
                    serial=f'127.0.0.1:{emulator[1]}',
                    name=emulator[0],
                    path=self.path,
                )


class EmulatorManager(EmulatorManagerBase):
    @cached_property
    def all_emulators(self) -> t.List[Emulator]:
        """
        Get all emulators installed on current computer.
        """
        paths = set()
        for folder in ['/Applications', os.path.expanduser('~/Applications')]:
            exe = os.path.join(folder, 'BlueStacks.app', BLUESTACKS_EXE)
            if os.path.exists(exe):
                paths.add(exe)

        if not paths:
            try:
                result = subprocess.run(
                    ['mdfind', f'kMDItemCFBundleIdentifier == "{BLUESTACKS_BUNDLE_ID}"'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                for bundle in result.stdout.splitlines():
                    exe = os.path.join(bundle, BLUESTACKS_EXE)
                    if os.path.exists(exe):
                        paths.add(exe)
            except (OSError, subprocess.SubprocessError):
                pass

        return [Emulator(path) for path in sorted(paths)]

    @cached_property
    def all_emulator_instances(self) -> t.List[EmulatorInstance]:
        """
        Get all emulator instances installed on current computer.
        """
        instances = []
        for emulator in self.all_emulators:
            instances += list(emulator.iter_instances())

        instances: t.List[EmulatorInstance] = sorted(instances, key=lambda x: str(x))
        return instances


if __name__ == '__main__':
    self = EmulatorManager()
    for emu in self.all_emulator_instances:
        print(emu)
