import os
from datetime import datetime

from PIL import Image

from pynput import keyboard
from module.config.config import AzurLaneConfig
from module.config.utils import alas_instance
from module.device.connection import Connection, ConnectionAttr
from module.device.device import Device
from module.logger import logger

"""
A tool to take screenshots on device

Usage:
    python -m dev_tools.screenshot
"""


class EmptyConnection(Connection):
    def __init__(self):
        ConnectionAttr.__init__(self, AzurLaneConfig('template'))

        logger.hr('Detect device')
        print()
        print('这里是你本机可用的模拟器serial:')
        devices = self.list_device()

        # Show available devices
        available = devices.select(status='device')
        for device in available:
            print(device.serial)
        if not len(available):
            print('No available devices')

        # Show unavailable devices if having any
        unavailable = devices.delete(available)
        if len(unavailable):
            print('Here are the devices detected but unavailable')
            for device in unavailable:
                print(f'{device.serial} ({device.status})')


def handle_sensitive_info(image):
    # Paint UID to black
    image[680:720, 0:180, :] = 0
    return image


_ = EmptyConnection()
name = input(
    '输入alas配置文件名称，或者模拟器serial，或者模拟器端口号: (默认输入 "alas"):\n'
    '例如："alas", "127.0.0.1:16384", "7555"\n'
)
name = name.strip().strip('"').strip()
if not name:
    name = 'alas'
if name.isdigit():
    name = f'127.0.0.1:{name}'
if name in alas_instance():
    print(f'{name} is an existing config file')
    device = Device(name)
else:
    print(f'{name} is a device serial')
    config = AzurLaneConfig('template')
    config.override(
        Emulator_Serial=name,
        Emulator_PackageName='com.miHoYo.hkrpg',
        Emulator_ScreenshotMethod='adb_nc',
    )
    device = Device(config)

output = './screenshots/dev_screenshots'
os.makedirs(output, exist_ok=True)
device.disable_stuck_detection()
device.screenshot_interval_set(0.)
print('')
print(f'截图将保存到: {output}')


def screenshot():
    print(f'截图中...')
    image = device.screenshot()
    now = datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S-%f')
    file = f'{output}/{now}.png'
    image = handle_sensitive_info(image)
    print(f'截图中...')
    Image.fromarray(image).save(file)
    print(f'截图已保存到: {file}')


# Bind global shortcut
GLOBAL_KEY = 'F3'


def on_press(key):
    if str(key) == f'Key.{GLOBAL_KEY.lower()}':
        screenshot()


listener = keyboard.Listener(on_press=on_press)
listener.start()

while 1:
    print()
    _ = input(f'按 <回车键> 或者按快捷键 <{GLOBAL_KEY}> 截一张图（快捷键全局生效）:')
    screenshot()
