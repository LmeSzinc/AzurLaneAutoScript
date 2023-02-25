import os
import typing as t
from dataclasses import dataclass

from deploy.utils import cached_property, iter_folder


def abspath(path):
    return os.path.abspath(path).replace('\\', '/')


@dataclass
class EmulatorInstanceBase:
    # Serial for adb connection
    serial: str
    # Emulator instance name, used for start/stop emulator
    name: str
    # Path to emulator .exe
    path: str

    def __str__(self):
        return f'{self.type}(serial="{self.serial}", name="{self.name}", path="{self.path}")'

    @cached_property
    def type(self) -> str:
        """
        Returns:
            str: Emulator type, such as Emulator.NoxPlayer
        """
        return EmulatorBase.path_to_type(self.path)

    @cached_property
    def emulator(self):
        """
        Returns:
            Emulator:
        """
        return EmulatorBase(self.path)

    def __eq__(self, other):
        if isinstance(other, str) and self.type == other:
            return True
        if isinstance(other, list) and self.type in other:
            return True
        if isinstance(other, EmulatorInstanceBase):
            return super().__eq__(other) and self.type == other.type
        return super().__eq__(other)

    def __hash__(self):
        return hash(str(self))

    def __bool__(self):
        return True


class EmulatorBase:
    NoxPlayer = 'NoxPlayer'
    NoxPlayer64 = 'NoxPlayer64'
    NoxPlayerFamily = [NoxPlayer, NoxPlayer64]
    BlueStacks4 = 'BlueStacks4'
    BlueStacks5 = 'BlueStacks5'
    BlueStacks4HyperV = 'BlueStacks4HyperV'
    BlueStacks5HyperV = 'BlueStacks5HyperV'
    BlueStacksFamily = [BlueStacks4, BlueStacks5]
    LDPlayer3 = 'LDPlayer3'
    LDPlayer4 = 'LDPlayer4'
    LDPlayer9 = 'LDPlayer9'
    LDPlayerFamily = [LDPlayer3, LDPlayer4, LDPlayer9]
    MumuPlayer = 'MumuPlayer'
    MumuPlayer9 = 'MumuPlayer9'
    MumuPlayer12 = 'MumuPlayer12'
    MumuPlayerFamily = [MumuPlayer, MumuPlayer9, MumuPlayer12]
    MemuPlayer = 'MemuPlayer'

    @classmethod
    def path_to_type(cls, path: str) -> str:
        """
        Args:
            path: Path to .exe file

        Returns:
            str: Emulator type, such as Emulator.NoxPlayer,
                or '' if this is not a emulator.
        """
        return ''

    def iter_instances(self):
        """
        Yields:
            EmulatorInstance: Emulator instances found in this emulator
        """
        return

    def __init__(self, path):
        # Path to .exe file
        self.path = path.replace('\\', '/')
        # Path to emulator folder
        self.dir = os.path.dirname(path)
        # str: Emulator type, or '' if this is not a emulator.
        self.type = self.__class__.path_to_type(path)

    def __eq__(self, other):
        if isinstance(other, str) and self.type == other:
            return True
        if isinstance(other, list) and self.type in other:
            return True
        return super().__eq__(other)

    def __str__(self):
        return f'{self.type}(path="{self.path}")'

    __repr__ = __str__

    def __hash__(self):
        return hash(self.path)

    def __bool__(self):
        return True

    def abspath(self, path, folder=None):
        if folder is None:
            folder = self.dir
        return abspath(os.path.join(folder, path))

    @classmethod
    def is_emulator(cls, path: str) -> bool:
        """
        Args:
            path: Path to .exe file.

        Returns:
            bool: If this is a emulator.
        """
        return bool(cls.path_to_type(path))

    def list_folder(self, folder, is_dir=False, ext=None):
        """
        Safely list files in a folder

        Args:
            folder:
            is_dir:
            ext:

        Returns:
            list[str]:
        """
        folder = self.abspath(folder)
        try:
            return list(iter_folder(folder, is_dir=is_dir, ext=ext))
        except FileNotFoundError:
            return []


class EmulatorManagerBase:
    @cached_property
    def all_emulators(self) -> t.List[EmulatorBase]:
        """
        Get all emulators installed on current computer.
        """
        return []

    @cached_property
    def all_emulator_instances(self) -> t.List[EmulatorInstanceBase]:
        """
        Get all emulator instances installed on current computer.
        """
        return []
