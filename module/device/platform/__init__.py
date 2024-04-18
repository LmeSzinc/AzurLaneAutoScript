import sys

if sys.platform == 'win32':
    from module.device.platform.platform_windows import PlatformWindows as Platform
elif sys.platform == 'linux':
    from module.device.platform.platform_linux import PlatformLinux as Platform
else:
    from module.device.platform.platform_base import PlatformBase as Platform
