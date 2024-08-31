import ctypes
import os
import subprocess
import typing as t
from dataclasses import dataclass
from functools import wraps

import cv2
import numpy as np

from module.base.decorator import cached_property
from module.device.method.utils import RETRY_TRIES, get_serial_pair, retry_sleep
from module.device.platform import Platform
from module.exception import RequestHumanTakeover
from module.logger import logger


class LDOpenGLIncompatible(Exception):
    pass


class LDOpenGLError(Exception):
    pass


def bytes_to_str(b: bytes) -> str:
    for encoding in ['utf-8', 'gbk']:
        try:
            return b.decode(encoding)
        except UnicodeDecodeError:
            pass
    return str(b)


@dataclass
class DataLDPlayerInfo:
    # Emulator instance index, starting from 0
    index: int
    # Instance name
    name: str
    # Handle of top window
    topWnd: int
    # Handle of bind window
    bndWnd: int
    # If instance is running, 1 for True, 0 for False
    sysboot: int
    # PID of the instance process, or -1 if instance is not running
    playerpid: int
    # PID of the vbox process, or -1 if instance is not running
    vboxpid: int
    # Resolution
    width: int
    height: int
    dpi: int

    def __post_init__(self):
        self.index = int(self.index)
        self.name = bytes_to_str(self.name)
        self.topWnd = int(self.topWnd)
        self.bndWnd = int(self.bndWnd)
        self.sysboot = int(self.sysboot)
        self.playerpid = int(self.playerpid)
        self.vboxpid = int(self.vboxpid)
        self.width = int(self.width)
        self.height = int(self.height)
        self.dpi = int(self.dpi)


class LDConsole:
    def __init__(self, ld_folder: str):
        """
        Args:
            ld_folder: Installation path of MuMu12, e.g. E:/ProgramFiles/LDPlayer9
                which should have a `ldconsole.exe` in it.
        """
        self.ld_console = os.path.abspath(os.path.join(ld_folder, './ldconsole.exe'))

    def subprocess_run(self, cmd, timeout=10):
        """
        Args:
            cmd (list):
            timeout (int):

        Returns:
            bytes:
        """
        cmd = [self.ld_console] + cmd
        logger.info(f'Execute: {cmd}')

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=False)
        except FileNotFoundError as e:
            logger.warning(f'warning when calling {cmd}, {str(e)}')
            raise LDOpenGLIncompatible(f'ld_folder does not have ldconsole.exe')
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            logger.warning(f'TimeoutExpired when calling {cmd}, stdout={stdout}, stderr={stderr}')
        return stdout

    def list2(self) -> t.List[DataLDPlayerInfo]:
        """
        > ldconsole.exe list2
        0,雷电模拟器,28053900,42935798,1,59776,36816,1280,720,240
        1,雷电模拟器-1,0,0,0,-1,-1,1280,720,240
        """
        out = []
        data = self.subprocess_run(['list2'])
        for row in data.strip().split(b'\n'):
            info = row.strip().split(b',')
            info = DataLDPlayerInfo(*info)
            out.append(info)
        return out


class IScreenShotClass:
    def __init__(self, ptr):
        self.ptr = ptr

        # Define in class since ctypes.WINFUNCTYPE is windows only
        cap_type = ctypes.WINFUNCTYPE(ctypes.c_void_p)
        release_type = ctypes.WINFUNCTYPE(None)
        self.class_cap = cap_type(1, "IScreenShotClass_Cap")
        # Keep reference count
        # so __del__ won't have an empty IScreenShotClass_Cap
        self.class_release = release_type(2, "IScreenShotClass_Release")

    def cap(self):
        return self.class_cap(self.ptr)

    def __del__(self):
        self.class_release(self.ptr)


def retry(func):
    @wraps(func)
    def retry_wrapper(self, *args, **kwargs):
        """
        Args:
            self (NemuIpcImpl):
        """
        init = None
        for _ in range(RETRY_TRIES):
            try:
                if callable(init):
                    retry_sleep(_)
                    init()
                return func(self, *args, **kwargs)
            # Can't handle
            except RequestHumanTakeover:
                break
            # Can't handle
            except LDOpenGLIncompatible as e:
                logger.error(e)
                break
            # NemuIpcError
            except LDOpenGLError as e:
                logger.error(e)

                def init():
                    pass
            # Unknown, probably a trucked image
            except Exception as e:
                logger.exception(e)

                def init():
                    pass

        logger.critical(f'Retry {func.__name__}() failed')
        raise RequestHumanTakeover

    return retry_wrapper


class LDOpenGLImpl:
    def __init__(self, ld_folder: str, instance_id: int):
        """
        Args:
            ld_folder: Installation path of MuMu12, e.g. E:/ProgramFiles/LDPlayer9
            instance_id: Emulator instance ID, starting from 0
        """
        ldopengl_dll = os.path.abspath(os.path.join(ld_folder, './ldopengl64.dll'))
        logger.info(
            f'LDOpenGL init, '
            f'ld_folder={ld_folder}, '
            f'ldopengl_dll={ldopengl_dll}, '
            f'instance_id={instance_id}'
        )
        self.console = LDConsole(ld_folder)
        self.info = self.get_player_info_by_index(instance_id)

        # Load dll
        try:
            self.lib = ctypes.WinDLL(ldopengl_dll)
        except OSError as e:
            logger.error(e)
            if not os.path.exists(ldopengl_dll):
                raise LDOpenGLIncompatible(
                    f'ldopengl_dll={ldopengl_dll} does not exist, '
                    f'ldopengl requires LDPlayer >= 9.0.75, please check your version'
                )
            else:
                raise LDOpenGLIncompatible(
                    f'ldopengl_dll={ldopengl_dll} exist, '
                    f'but cannot be loaded'
                )
        self.lib.CreateScreenShotInstance.restype = ctypes.c_void_p

        # Get screenshot instance
        instance_ptr = ctypes.c_void_p(self.lib.CreateScreenShotInstance(instance_id, self.info.playerpid))
        self.screenshot_instance = IScreenShotClass(instance_ptr)

    def get_player_info_by_index(self, instance_id: int):
        """
        Args:
            instance_id:

        Returns:
            DataLDPlayerInfo:

        Raises:
            LDOpenGLError:
        """
        for info in self.console.list2():
            if info.index == instance_id:
                logger.info(f'Match LDPlayer instance: {info}')
                if not info.sysboot:
                    raise LDOpenGLError('Trying to connect LDPlayer instance but emulator is not running')
                return info
        raise LDOpenGLError(f'No LDPlayer instance with index {instance_id}')

    @retry
    def screenshot(self):
        """
        Returns:
            np.ndarray: Image array in BGR color space
                Note that image is upside down
        """
        width, height = self.info.width, self.info.height

        img_ptr = self.screenshot_instance.cap()
        # ValueError: NULL pointer access
        if img_ptr is None:
            raise LDOpenGLError('Empty image pointer')

        img = ctypes.cast(img_ptr, ctypes.POINTER(ctypes.c_ubyte * (height * width * 3))).contents

        image = np.ctypeslib.as_array(img).copy().reshape((height, width, 3))
        return image

    @staticmethod
    def serial_to_id(serial: str):
        """
        Predict instance ID from serial
        E.g.
            "127.0.0.1:5555" -> 0
            "127.0.0.1:5557" -> 1
            "emulator-5554" -> 0

        Returns:
            int: instance_id, or None if failed to predict
        """
        serial, _ = get_serial_pair(serial)
        try:
            port = int(serial.split(':')[1])
        except (IndexError, ValueError):
            return None
        if 5555 <= port <= 5555 + 32:
            return int((port - 5555) // 2)
        return None


class LDOpenGL(Platform):
    @cached_property
    def ldopengl(self):
        """
        Initialize a ldopengl implementation
        """
        # Try existing settings first
        if self.config.EmulatorInfo_path:
            folder = os.path.abspath(os.path.join(self.config.EmulatorInfo_path, '../'))
            index = LDOpenGLImpl.serial_to_id(self.serial)
            if index is not None:
                try:
                    return LDOpenGLImpl(
                        ld_folder=folder,
                        instance_id=index,
                    )
                except (LDOpenGLIncompatible, LDOpenGLError) as e:
                    logger.error(e)
                    logger.error('Emulator info incorrect')

        # Search emulator instance
        # with E:/ProgramFiles/LDPlayer9/dnplayer.exe
        # installation path is E:/ProgramFiles/LDPlayer9
        if self.emulator_instance is None:
            logger.error('Unable to use LDOpenGL because emulator instance not found')
            raise RequestHumanTakeover
        try:
            return LDOpenGLImpl(
                ld_folder=self.emulator_instance.emulator.abspath('./'),
                instance_id=self.emulator_instance.LDPlayer_id,
            )
        except (LDOpenGLIncompatible, LDOpenGLError) as e:
            logger.error(e)
            logger.error('Unable to initialize LDOpenGL')
            raise RequestHumanTakeover

    def ldopengl_available(self) -> bool:
        if not self.is_ldplayer_bluestacks_family:
            return False

        try:
            _ = self.ldopengl
        except RequestHumanTakeover:
            return False
        return True

    def screenshot_ldopengl(self):
        image = self.ldopengl.screenshot()

        cv2.flip(image, 0, dst=image)
        cv2.cvtColor(image, cv2.COLOR_BGR2RGB, dst=image)
        return image


if __name__ == '__main__':
    ld = LDOpenGLImpl('E:/ProgramFiles/LDPlayer9', instance_id=1)
    for _ in range(5):
        import time

        start = time.time()
        ld.screenshot()
        print(time.time() - start)
