import re
from typing import Any, Generator, Iterable
from shlex import split as split_
from os.path import dirname
import threading

from ctypes import addressof, byref, create_unicode_buffer, sizeof, wstring_at
from ctypes.wintypes import HWND, LPARAM, DWORD, ULONG

from module.device.platform.emulator_windows import Emulator
from module.device.platform.winapi import *
from module.base.timer import Timer
from module.logger import logger

__all__ = [
    'close_handle', '__yield_entries', '_enum_processes', '_enum_threads',
    'get_focused_window', 'set_focus_to_window', 'refresh_window',
    'execute', 'terminate_process', 'get_hwnds', 'get_cmdline',
    'kill_process_by_regex', '__get_time', '_get_process_creation_time',
    '_get_thread_creation_time', 'get_thread', '_get_process', 'get_process',
    'switch_window', 'get_parent_pid', 'get_exit_code', 'is_running',
    'send_message_box'
]

_lock = threading.Lock()

def close_handle(handles: Iterable[Any], *args, fclose=None):
    from itertools import chain

    if fclose is None:
        fclose = CloseHandle
    closed = []

    for handle in chain(handles, args):
        if isinstance(handle, (int, c_void_p)):
            fclose(handle)
            closed.append(handle)
            continue
        report(
            f"Expected a int or c_void_p, but got {type(handle).__name__}",
            r_status=False, level=30, r_exc=False
        )

    if len(closed):
        logger.info(f"Closed handles: {closed}")
        return True

    report(
        f"All handles are unavailable, please check the running environment",
        r_status=False, r_exc=False
    )
    return False

def __yield_entries(entry32, snapshot, func):
    while 1:
        if not func(snapshot, byref(entry32)):
            break
        yield entry32

    # Finished querying
    errcode = GetLastError()
    assert errcode == ERROR_NO_MORE_FILES, report(f"{func.__name__} failed", status=errcode)
    report("Finished querying", status=errcode, use_log=False, exc=IterationFinished)

def _enum_processes() -> Generator[PROCESSENTRY32W, None, None]:
    with create_snapshot(TH32CS_SNAPPROCESS) as snapshot, PROCESSENTRY32W(sizeof(PROCESSENTRY32W)) as lppe32:
        assert Process32First(snapshot, byref(lppe32)), report("Process32First failed")
        yield lppe32
        yield from __yield_entries(lppe32, snapshot, Process32Next)

def _enum_threads() -> Generator[THREADENTRY32, None, None]:
    with create_snapshot(TH32CS_SNAPTHREAD) as snapshot, THREADENTRY32(sizeof(THREADENTRY32)) as lpte32:
        assert Thread32First(snapshot, byref(lpte32)), report("Thread32First failed")
        yield lpte32
        yield from __yield_entries(lpte32, snapshot, Thread32Next)

def get_focused_window():
    hwnd = HWND(GetForegroundWindow())
    wp = WINDOWPLACEMENT(sizeof(WINDOWPLACEMENT))

    if not GetWindowPlacement(hwnd, byref(wp)):
        report("Failed to get windowplacement", level=30, r_exc=False)
        wp = None

    return hwnd, wp

def set_focus_to_window(focusedwindow):
    SetForegroundWindow(focusedwindow[0])

    if focusedwindow[1] is None:
        ShowWindow(focusedwindow[0], SW_SHOWNORMAL)
        return

    ShowWindow(focusedwindow[0], focusedwindow[1].showCmd)
    SetWindowPlacement(focusedwindow[0], byref(focusedwindow[1]))

def refresh_window(focusedwindow, max_attempts=10, interval=0.5):
    from itertools import combinations

    with _lock:
        attempts = 0
        prevwindow = None

        unique = lambda *args: all(x[0].value != y[0].value for x, y in combinations(args, 2))
        interval = Timer(interval).start()

        while attempts < max_attempts:
            currentwindow = get_focused_window()
            if prevwindow and unique(currentwindow, prevwindow, focusedwindow):
                break

            if unique(focusedwindow, currentwindow):
                logger.info(f"Current window is {currentwindow[0]}, flash back to {focusedwindow[0]}")
                set_focus_to_window(focusedwindow)
                attempts += 1
                interval.wait()
                interval.reset()
                continue

            attempts += 1
            interval.wait()
            interval.reset()

            prevwindow = currentwindow

        del focusedwindow, currentwindow, prevwindow

def execute(command, silentstart, start):
    # TODO:Create Process with non-administrator privileges
    logger.info(f"Create Process: {command}")
    focusedwindow               = get_focused_window()
    if start and silentstart:
        refresh_thread = threading.Thread(target=refresh_window, name='Refresh-Thread', args=(focusedwindow,))
        refresh_thread.start()

    lpApplicationName           = split_(command)[0]
    lpCommandLine               = command
    lpProcessAttributes         = None
    lpThreadAttributes          = None
    bInheritHandles             = False
    dwCreationFlags             = (
        CREATE_NEW_CONSOLE |
        NORMAL_PRIORITY_CLASS |
        CREATE_NEW_PROCESS_GROUP |
        CREATE_DEFAULT_ERROR_MODE |
        CREATE_UNICODE_ENVIRONMENT
    )
    lpEnvironment               = None
    lpCurrentDirectory          = dirname(lpApplicationName)
    lpStartupInfo               = STARTUPINFOW(
        cb                      = sizeof(STARTUPINFOW),
        dwFlags                 = STARTF_USESHOWWINDOW,
    )
    if start:
        lpStartupInfo.wShowWindow = SW_FORCEMINIMIZE if silentstart else SW_MINIMIZE
    else:
        lpStartupInfo.wShowWindow = SW_HIDE
    lpProcessInformation        = PROCESS_INFORMATION()

    assert CreateProcessW(
        lpApplicationName,
        lpCommandLine,
        lpProcessAttributes,
        lpThreadAttributes,
        bInheritHandles,
        dwCreationFlags,
        lpEnvironment,
        lpCurrentDirectory,
        byref(lpStartupInfo),
        byref(lpProcessInformation)
    ),  report("Failed to start emulator", exc=EmulatorLaunchFailedError)

    if start:
        wait = WaitForInputIdle(lpProcessInformation[0], INFINITE)
        assert wait == 0, \
            report("Failed to start emulator", exc=EmulatorLaunchFailedError)
    else:
        logger.info(f"Close useless handles")
        close_handle(lpProcessInformation[:2])
        lpProcessInformation = None

    return lpProcessInformation, focusedwindow

def terminate_process(pid):
    with open_process(PROCESS_TERMINATE, pid) as hProcess:
        assert TerminateProcess(hProcess, 0), \
            report(f"Failed to terminate process: {pid}", level=30, r_exc=False)
    return True

def get_hwnds(pid):
    logger.hr("Get hwnds", level=3)
    hwnds = []

    @EnumWindowsProc
    def callback(hwnd: HWND, lparam: LPARAM):  # DO NOT DELETE THIS PARAMETER!!!
        processid = DWORD()
        GetWindowThreadProcessId(hwnd, byref(processid))
        if processid.value == pid:
            hwnds.append(HWND(hwnd))
        return True

    assert EnumWindows(callback, LPARAM(0)), report("Failed to get hwnds")

    if not hwnds:
        report("Hwnd not found", level=30, exc=HwndNotFoundError)
    logger.attr("Emulator hwnds", hwnds)
    return hwnds

def get_cmdline(pid):
    try:
        with open_process(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, pid) as hProcess:
            # Query process infomation
            pbi = PROCESS_BASIC_INFORMATION()
            returnlength = ULONG(sizeof(pbi))
            status = NtQueryInformationProcess(hProcess, 0, byref(pbi), sizeof(pbi), byref(returnlength))
            assert status == STATUS_SUCCESS, \
                report(f"NtQueryInformationProcess failed. Status: 0x{status:08x}", r_status=False, level=30)

            # Read PEB
            peb = PEB()
            assert ReadProcessMemory(hProcess, pbi.PebBaseAddress, byref(peb), sizeof(peb), None), \
                report("Failed to read PEB", level=30)

            # Read process parameters
            upp = RTL_USER_PROCESS_PARAMETERS()
            assert ReadProcessMemory(hProcess, peb.ProcessParameters, byref(upp), sizeof(upp), None), \
                report("Failed to read process parameters", level=30)

            # Read command line
            commandLine = create_unicode_buffer(upp.CommandLine.Length // 2)
            assert ReadProcessMemory(hProcess, upp.CommandLine.Buffer, commandLine, upp.CommandLine.Length, None), \
                report("Failed to read command line", level=30)

            cmdline = wstring_at(addressof(commandLine), len(commandLine))
    except OSError:
        return ''
    return hex_or_normalize_path(cmdline)

def kill_process_by_regex(regex):
    count = 0

    try:
        for lppe32 in _enum_processes():
            pid     = lppe32.th32ProcessID
            cmdline = get_cmdline(lppe32.th32ProcessID)

            if not re.search(regex, cmdline):
                continue

            logger.info(f'Kill emulator: {cmdline}')
            terminate_process(pid)
            count += 1
    except IterationFinished:
        return count

def __get_time(fopen, fgettime, access, identification, select=0):
    with fopen(access, identification, False, False) as handle:
        ti = TIMEINFO()
        if not fgettime(handle, byref(ti.CreationTime), byref(ti.ExitTime), byref(ti.KernelTime), byref(ti.UserTime)):
            return
        return ti[select].to_int()

def _get_process_creation_time(pid):
    access = PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
    return __get_time(open_process, GetProcessTimes, access, pid, select=0)

def _get_thread_creation_time(tid):
    return __get_time(open_thread, GetThreadTimes, THREAD_QUERY_INFORMATION, tid, select=0)

def get_thread(pid):
    mainthreadid    = 0
    minstarttime    = MAXULONGLONG
    try:
        for lpte32 in _enum_threads():
            if lpte32.th32OwnerProcessID != pid:
                continue

            # In general, the first tid obtained by traversing is always the main tid, so these code can be commented.
            threadstarttime = _get_thread_creation_time(lpte32.th32ThreadID)
            if threadstarttime is None or threadstarttime >= minstarttime:
                continue

            minstarttime = threadstarttime
            mainthreadid = lpte32.th32ThreadID
    except IterationFinished:
        return mainthreadid

def _get_process(pid):
    tid = get_thread(pid)
    pi = PROCESS_INFORMATION(dwProcessId=pid, dwThreadId=tid)
    try:
        hProcess = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        assert hProcess is not None, \
            report("OpenProcess failed", level=30)

        hThread = OpenThread(THREAD_ALL_ACCESS, False, tid)
        if hThread is None:
            CloseHandle(hProcess)
            report("OpenThread failed", level=30)

        pi[:2] = hProcess, hThread
    except OSError as e:
        logger.warning(f"Failed to get process and thread handles: {e}")
    finally:
        logger.attr("Emulator Process", pi)
        return pi

def get_process(instance):
    logger.hr("Get Process", level=3)
    for lppe32 in _enum_processes():
        pid = lppe32.th32ProcessID
        cmdline = get_cmdline(pid)
        if not cmdline:
            continue

        if not instance.path.lower() in cmdline.lower():
            continue

        if instance == Emulator.MuMuPlayer12:
            match = re.search(r'-v\s*(\d+)', cmdline)
            if match is None:
                return _get_process(pid)
            if match and int(match.group(1)) == instance.MuMuPlayer12_id:
                return _get_process(pid)
        elif instance == Emulator.LDPlayerFamily:
            match = re.search(r'index=\s*(\d+)', cmdline)
            if match and int(match.group(1)) == instance.LDPlayer_id:
                return _get_process(pid)
        else:
            match = re.search(fr'{instance.name}(\s+|$)', cmdline)
            if match and match.group(0).strip() == instance.name:
                return _get_process(pid)

def switch_window(hwnds=None, arg=None):
    for hwnd in hwnds:
        if not GetWindow(hwnd, GW_CHILD):
            continue
        ShowWindow(hwnd, arg)
    return True

def get_parent_pid(pid):
    try:
        with open_process(PROCESS_QUERY_INFORMATION, pid) as hProcess:
            # Query process infomation
            pbi = PROCESS_BASIC_INFORMATION()
            returnlength = ULONG(sizeof(pbi))
            status = NtQueryInformationProcess(hProcess, 0, byref(pbi), returnlength, byref(returnlength))
            assert status == STATUS_SUCCESS, \
                report(f"NtQueryInformationProcess failed. Status: 0x{status:08x}", r_status=False, level=30)
    except OSError:
        return -1
    return pbi.InheritedFromUniqueProcessId

def get_exit_code(pid):
    try:
        with open_process(PROCESS_QUERY_INFORMATION, pid) as hProcess:
            exit_code = ULONG()
            assert GetExitCodeProcess(hProcess, byref(exit_code)), \
                report("Failed to get Exit code", level=30)
    except OSError:
        return -1
    return exit_code.value

def is_running(pid=0, ppid=0):
    if pid and get_exit_code(pid) != STILL_ACTIVE:
        return False
    if ppid and ppid != get_parent_pid(pid):
        return False
    return True

def send_message_box(
        text='Hello World!', caption='ALAS Message Box', style=None,
        helpid=None, callback=None, p=None, s=None
):
    try:
        hwnds = get_hwnds(GetCurrentProcessId())
        hwndOwner = next((hwnd for hwnd in hwnds if GetWindow(hwnd, GW_CHILD)), None)
    except (HwndNotFoundError, StopIteration):
        # TODO:CreateWindowExW
        hwndOwner = None

    if style is None:
        style = MB_YESNOCANCEL | MB_ICONINFORMATION

    mbparams = MSGBOXPARAMSW(sizeof(MSGBOXPARAMSW), hwndOwner, GetModuleHandleW(None), text, caption, style)

    if style & MB_HELP == MB_HELP:
        if isinstance(helpid, int) and callable(callback):
            mbparams[7:9] = helpid, callback
        else:
            mbparams[8] = None

    if all(isinstance(i, int) for i in (p, s)):
        mbparams.dwLanguageId = (s & 0xffff) << 10 | (p & 0xffff)

    result = MessageBoxIndirectW(byref(mbparams))

    return result

@MSGBOXCALLBACK
def MsgBoxCallback(lphelpinfo):
    if lphelpinfo.contents.dwContextId == 0x1:
        MessageBoxW(None, "0x1 help", "HELP", 0)
    elif lphelpinfo.contents.dwContextId == 0x10:
        MessageBoxW(None, "0x10 help", "HELP", 0)
    elif lphelpinfo.contents.dwContextId == 0x100:
        MessageBoxW(None, "0x100 help", "HELP", 0)
    else:
        MessageBoxW(None, "Default help", "HELP", 0)

if __name__ == '__main__':
    ret = send_message_box(
        style=MB_HELP | MB_YESNOCANCEL | MB_ICONERROR,
        helpid=0x10, callback=MsgBoxCallback
    )
    print(ret)
