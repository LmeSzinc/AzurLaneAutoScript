from module.device.env import IS_WINDOWS, IS_MACINTOSH

if IS_WINDOWS:
    from module.device.platform.platform_windows import PlatformWindows as Platform
elif IS_MACINTOSH:
    from module.device.platform.platform_mac import PlatformMac as Platform
else:
    from module.device.platform.platform_base import PlatformBase as Platform
