from module.device.env import IS_LINUX, IS_WINDOWS

if IS_WINDOWS:
    from module.device.platform.platform_windows import PlatformWindows as Platform
elif IS_LINUX:
    from module.device.platform.platform_linux import PlatformLinux as Platform
else:
    from module.device.platform.platform_base import PlatformBase as Platform
