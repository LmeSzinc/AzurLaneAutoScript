import socket
import struct
import threading
import time
import typing as t
from time import sleep

import numpy as np
from adbutils import _AdbStreamConnection, AdbError, Network

from module.base.decorator import cached_property
from module.base.timer import Timer
from module.device.connection import Connection
from module.device.method.scrcpy.control import ControlSender
from module.device.method.scrcpy.options import ScrcpyOptions
from module.device.method.utils import recv_all
from module.exception import RequestHumanTakeover
from module.logger import logger


class ScrcpyError(Exception):
    pass


class ScrcpyCore(Connection):
    """
    Scrcpy: https://github.com/Genymobile/scrcpy
    Module from https://github.com/leng-yue/py-scrcpy-client
    """

    _scrcpy_last_frame: t.Optional[np.ndarray] = None
    _scrcpy_last_frame_time: float = 0.

    _scrcpy_alive = False
    _scrcpy_server_stream: t.Optional[_AdbStreamConnection] = None
    _scrcpy_video_socket: t.Optional[socket.socket] = None
    _scrcpy_control_socket: t.Optional[socket.socket] = None
    _scrcpy_control_socket_lock = threading.Lock()

    _scrcpy_stream_loop_thread = None
    _scrcpy_resolution: t.Tuple[int, int] = (1280, 720)

    @cached_property
    def _scrcpy_control(self) -> ControlSender:
        return ControlSender(self)

    def scrcpy_init(self):
        self._scrcpy_server_stop()

        logger.hr('Scrcpy init')
        logger.info(f'pushing {self.config.SCRCPY_FILEPATH_LOCAL}')
        self.adb_push(self.config.SCRCPY_FILEPATH_LOCAL, self.config.SCRCPY_FILEPATH_REMOTE)

        self._scrcpy_alive = False
        self.scrcpy_ensure_running()

    def scrcpy_ensure_running(self):
        if not self._scrcpy_alive:
            with self._scrcpy_control_socket_lock:
                self._scrcpy_server_start()

    def _scrcpy_server_start(self):
        """
        Connect to scrcpy server, there will be two sockets, video and control socket.

        Raises:
            ScrcpyError:
        """
        logger.hr('Scrcpy server start')
        commands = ScrcpyOptions.command_v120(jar_path=self.config.SCRCPY_FILEPATH_REMOTE)
        self._scrcpy_server_stream: _AdbStreamConnection = self.adb.shell(
            commands,
            stream=True,
        )

        logger.info('Create server stream')
        ret = self._scrcpy_server_stream.read(10)
        # b'Aborted \r\n'
        # Probably because file not exists
        if b'Aborted' in ret:
            raise ScrcpyError('Aborted')
        if ret == b'[server] E':
            # [server] ERROR: ...
            ret += recv_all(self._scrcpy_server_stream)
            logger.error(ret)
            # java.lang.IllegalArgumentException: The server version (1.25) does not match the client (...)
            if b'does not match the client' in ret:
                raise ScrcpyError('Server version does not match the client')
            else:
                raise ScrcpyError('Unknown scrcpy error')
        else:
            # [server] INFO: Device: ...
            ret += self._scrcpy_receive_from_server_stream()
            logger.info(ret)
            pass

        logger.info('Create video socket')
        timeout = Timer(3).start()
        while 1:
            if timeout.reached():
                raise ScrcpyError('Connect scrcpy-server timeout')

            try:
                self._scrcpy_video_socket = self.adb.create_connection(
                    Network.LOCAL_ABSTRACT, "scrcpy"
                )
                break
            except AdbError:
                sleep(0.1)
        dummy_byte = self._scrcpy_video_socket.recv(1)
        if not len(dummy_byte) or dummy_byte != b"\x00":
            raise ScrcpyError('Did not receive Dummy Byte from video stream')

        logger.info('Create control socket')
        self._scrcpy_control_socket = self.adb.create_connection(
            Network.LOCAL_ABSTRACT, "scrcpy"
        )

        logger.info('Fetch device info')
        device_name = self._scrcpy_video_socket.recv(64).decode("utf-8").rstrip("\x00")
        if len(device_name):
            logger.attr('Scrcpy Device', device_name)
        else:
            raise ScrcpyError('Did not receive Device Name')
        ret = self._scrcpy_video_socket.recv(4)
        self._scrcpy_resolution = struct.unpack(">HH", ret)
        logger.attr('Scrcpy Resolution', self._scrcpy_resolution)

        self._scrcpy_video_socket.setblocking(False)
        self._scrcpy_alive = True

        logger.info('Start video stream loop thread')
        self._scrcpy_stream_loop_thread = threading.Thread(
            target=self._scrcpy_stream_loop, daemon=True
        )
        self._scrcpy_stream_loop_thread.start()
        while 1:
            if self._scrcpy_stream_loop_thread is not None and self._scrcpy_stream_loop_thread.is_alive():
                break
            self.sleep(0.001)

        logger.info('Scrcpy server is up')

    def _scrcpy_server_stop(self):
        """
        Stop listening (both threaded and blocked)
        """
        logger.hr('Scrcpy server stop')
        # err = self._scrcpy_receive_from_server_stream()
        # if err:
        #     logger.error(err)

        self._scrcpy_alive = False
        if self._scrcpy_server_stream is not None:
            try:
                self._scrcpy_server_stream.close()
            except Exception:
                pass

        if self._scrcpy_control_socket is not None:
            try:
                self._scrcpy_control_socket.close()
            except Exception:
                pass

        if self._scrcpy_video_socket is not None:
            try:
                self._scrcpy_video_socket.close()
            except Exception:
                pass

        logger.info('Scrcpy server stopped')

    def _scrcpy_receive_from_server_stream(self):
        if self._scrcpy_server_stream is not None:
            try:
                return self._scrcpy_server_stream.conn.recv(4096)
            except Exception:
                pass

    def _scrcpy_stream_loop(self) -> None:
        """
        Core loop for video parsing
        """
        try:
            from av.codec import CodecContext
            from av.error import InvalidDataError
        except ImportError as e:
            logger.error(e)
            logger.error('You must have `av` installed to use scrcpy screenshot, please update dependencies')
            raise RequestHumanTakeover

        codec = CodecContext.create("h264", "r")
        while self._scrcpy_alive:
            try:
                raw_h264 = self._scrcpy_video_socket.recv(0x10000)
                if raw_h264 == b"":
                    raise ScrcpyError("Video stream is disconnected")
                packets = codec.parse(raw_h264)
                for packet in packets:
                    frames = codec.decode(packet)
                    for frame in frames:
                        # logger.info('frame received')
                        frame = frame.to_ndarray(format="rgb24")
                        self._scrcpy_last_frame = frame
                        self._scrcpy_last_frame_time = time.time()
                        self._scrcpy_resolution = (frame.shape[1], frame.shape[0])
            except (BlockingIOError, InvalidDataError):
                # only return nonempty frames, may block cv2 render thread
                time.sleep(0.001)
            except (ConnectionError, OSError) as e:  # Socket Closed
                if self._scrcpy_alive:
                    logger.error(f'_scrcpy_stream_loop_thread: {repr(e)}')
                    raise

        raise ScrcpyError('_scrcpy_stream_loop stopped')
