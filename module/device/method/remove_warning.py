from typing import overload


@overload
def remove_shell_warning(s: bytes) -> bytes: ...


@overload
def remove_shell_warning(s: str) -> str: ...


def remove_shell_warning(s):
    """
    Remove warnings from shell

    1. Warnings in VMOS shell
    https://github.com/LmeSzinc/AzurLaneAutoScript/issues/1425

    WARNING: linker: [vdso]: unused DT entry: type 0x70000001 arg 0x0\n
    \x89PNG\r\n\x1a\n\x00\x00\x00\rIH...

    2. This linker thingy might appear multiple times when executing multiple commands

    mek_8q:/dev # getprop | grep gnss
    WARNING: linker: Warning: "[vdso]" unused DT entry: unknown processor-specific (type 0x70000001 arg 0x0) (ignoring)
    WARNING: linker: Warning: "[vdso]" unused DT entry: unknown processor-specific (type 0x70000001 arg 0x0) (ignoring)
    [init.svc.gnss_service]: [running]
    [init.svc_debug_pid.gnss_service]: [406]
    [ro.boottime.gnss_service]: [27308752875]

    Args:
        s (str | bytes): bytes or str

    Returns:
        str | bytes: Shell output with warnings removed
    """
    if isinstance(s, bytes):
        while 1:
            if s.startswith(b'WARNING: linker:'):
                _, _, s = s.partition(b'\n')
            else:
                break
    elif isinstance(s, str):
        while 1:
            if s.startswith('WARNING: linker:'):
                _, _, s = s.partition('\n')
            else:
                break

    return s


@overload
def remove_screenshot_warning(s: bytes) -> bytes: ...


@overload
def remove_screenshot_warning(s: str) -> str: ...


def remove_screenshot_warning(s):
    """
    Remove warnings when taking screenshot

    1. Errors in waydroid screencap render
    https://github.com/LmeSzinc/AzurLaneAutoScript/issues/4760

    Failed to create //.cache for shader cache (Read-only file system)---disabling.\n
    \x89PNG...

    2. Warning when taking screenshot from multiscreen device

    [Warning] Multiple displays were found, but no display id was specified! Defaulting to the first display found,
    however this default is not guaranteed to be consistent across captures.\n
    A display id should be specified.\n
    See "dumpsys SurfaceFlinger --display-id" for valid display IDs.\n
    \x89PNG...

    3. Another format of multiscreen warning
    https://github.com/LmeSzinc/AzurLaneAutoScript/issues/5682

    [Warning] Multiple displays were found, but no display id was specified! Defaulting to the first display found,
    however this default is not guaranteed to be consistent across captures. A display id should be specified.\n
    A display ID can be specified with the [-d display-id] option.\n
    See "dumpsys SurfaceFlinger --display-id" for valid display IDs.\n
    \x89PNG...

    4. Unknown header on VMOS PRO screenshot
    https://github.com/LmeSzinc/AzurLaneAutoScript/pull/940

    long long=8 fun*=10\n
    \x89PNG...

    5. Warning from AMD GPU driver when running redroid on minimal linux system (typically a NAS)
    https://github.com/LmeSzinc/AzurLaneAutoScript/issues/5697

    amdgpu: os_same_file_description couldn't determine if two DRM fds reference the same file description.\n
    If they do, bad things may happen!\n
    \x89PNG...

    Args:
        s (str | bytes): bytes or str

    Returns:
        str | bytes: Screenshot data with warnings removed
    """
    if isinstance(s, bytes):
        if s.startswith(b'Failed to create'):
            _, _, s = s.partition(b'\n')
        if s.startswith(b'[Warning] Multiple displays'):
            _, _, s = s.partition(b'\n')
            if s.startswith(b'A display id') or s.startswith(b'A display ID'):
                _, _, s = s.partition(b'\n')
                if s.startswith(b'See "dumpsys'):
                    _, _, s = s.partition(b'\n')
        if s.startswith(b'long long=8'):
            _, _, s = s.partition(b'\n')
        if s.startswith(b'amdgpu:'):
            _, _, s = s.partition(b'\n')
            if s.startswith(b'If they do'):
                _, _, s = s.partition(b'\n')

    elif isinstance(s, str):
        if s.startswith('Failed to create'):
            _, _, s = s.partition('\n')
        if s.startswith('[Warning] Multiple displays'):
            _, _, s = s.partition('\n')
            if s.startswith('A display id') or s.startswith('A display ID'):
                _, _, s = s.partition('\n')
                if s.startswith('See "dumpsys'):
                    _, _, s = s.partition('\n')
        if s.startswith('long long=8'):
            _, _, s = s.partition('\n')
        if s.startswith('amdgpu:'):
            _, _, s = s.partition('\n')
            if s.startswith('If they do'):
                _, _, s = s.partition('\n')

    return s
