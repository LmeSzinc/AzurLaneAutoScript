import functools
import struct
import time

import module.device.method.scrcpy.const as const


def inject(control_type: int):
    """
    Inject control code, with this inject, we will be able to do unit test

    Args:
        control_type: event to send, TYPE_*
    """

    def wrapper(f):
        @functools.wraps(f)
        def inner(self, *args, **kwargs):
            package = struct.pack(">B", control_type) + f(self, *args, **kwargs)
            if self.control_socket is not None:
                with self.control_socket_lock:
                    self.control_socket.send(package)
            return package

        return inner

    return wrapper


class ControlSender:
    def __init__(self, parent):
        self.parent = parent

    @property
    def control_socket(self):
        return self.parent._scrcpy_control_socket

    @property
    def control_socket_lock(self):
        return self.parent._scrcpy_control_socket_lock

    @property
    def resolution(self):
        return self.parent._scrcpy_resolution

    @inject(const.TYPE_INJECT_KEYCODE)
    def keycode(self, keycode: int, action: int = const.ACTION_DOWN, repeat: int = 0) -> bytes:
        """
        Send keycode to device

        Args:
            keycode: const.KEYCODE_*
            action: ACTION_DOWN | ACTION_UP
            repeat: repeat count
        """
        return struct.pack(">Biii", action, keycode, repeat, 0)

    @inject(const.TYPE_INJECT_TEXT)
    def text(self, text: str) -> bytes:
        """
        Send text to device

        Args:
            text: text to send
        """

        buffer = text.encode("utf-8")
        return struct.pack(">i", len(buffer)) + buffer

    @inject(const.TYPE_INJECT_TOUCH_EVENT)
    def touch(self, x: int, y: int, action: int = const.ACTION_DOWN, touch_id: int = -1) -> bytes:
        """
        Touch screen

        Args:
            x: horizontal position
            y: vertical position
            action: ACTION_DOWN | ACTION_UP | ACTION_MOVE
            touch_id: Default using virtual id -1, you can specify it to emulate multi finger touch
        """
        x, y = max(x, 0), max(y, 0)
        return struct.pack(
            ">BqiiHHHi",
            action,
            touch_id,
            int(x),
            int(y),
            int(self.resolution[0]),
            int(self.resolution[1]),
            0xFFFF,
            1,
        )

    @inject(const.TYPE_INJECT_SCROLL_EVENT)
    def scroll(self, x: int, y: int, h: int, v: int) -> bytes:
        """
        Scroll screen

        Args:
            x: horizontal position
            y: vertical position
            h: horizontal movement
            v: vertical movement
        """

        x, y = max(x, 0), max(y, 0)
        return struct.pack(
            ">iiHHii",
            int(x),
            int(y),
            int(self.resolution[0]),
            int(self.resolution[1]),
            int(h),
            int(v),
        )


    def swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        move_step_length: int = 5,
        move_steps_delay: float = 0.005,
    ) -> None:
        """
        Swipe on screen

        Args:
            start_x: start horizontal position
            start_y: start vertical position
            end_x: start horizontal position
            end_y: end vertical position
            move_step_length: length per step
            move_steps_delay: sleep seconds after each step
        :return:
        """

        self.touch(start_x, start_y, const.ACTION_DOWN)
        next_x = start_x
        next_y = start_y

        if end_x > self.resolution[0]:
            end_x = self.resolution[0]

        if end_y > self.resolution[1]:
            end_y = self.resolution[1]

        decrease_x = start_x > end_x
        decrease_y = start_y > end_y
        while True:
            if decrease_x:
                next_x -= move_step_length
                if next_x < end_x:
                    next_x = end_x
            else:
                next_x += move_step_length
                if next_x > end_x:
                    next_x = end_x

            if decrease_y:
                next_y -= move_step_length
                if next_y < end_y:
                    next_y = end_y
            else:
                next_y += move_step_length
                if next_y > end_y:
                    next_y = end_y

            self.touch(next_x, next_y, const.ACTION_MOVE)

            if next_x == end_x and next_y == end_y:
                self.touch(next_x, next_y, const.ACTION_UP)
                break
            time.sleep(move_steps_delay)
