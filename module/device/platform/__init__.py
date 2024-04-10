import sys

if sys.platform == 'win32':
    from module.device.platform.platform_windows import PlatformWindows as Platform
else:
    from module.device.platform.platform_base import PlatformBase as Platform
