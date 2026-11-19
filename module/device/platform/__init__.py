from module.device.env import IS_MACINTOSH, IS_WINDOWS

if IS_WINDOWS:
    from module.device.platform.platform_windows import PlatformWindows as Platform
elif IS_MACINTOSH:
    from module.device.platform.platform_macos import PlatformMacOS as Platform
else:
    from module.device.platform.platform_base import PlatformBase as Platform
