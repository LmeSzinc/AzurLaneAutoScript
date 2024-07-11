from module.device.env import IS_WINDOWS

if IS_WINDOWS:
    from module.device.platform.platform_windows import PlatformWindows as Platform
else:
    from module.device.platform.platform_base import PlatformBase as Platform
