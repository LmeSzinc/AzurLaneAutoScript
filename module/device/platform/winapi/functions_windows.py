from abc import ABCMeta, abstractmethod
from typing import Any, Callable, Optional, Union

from ctypes import POINTER, WINFUNCTYPE, WinDLL, c_size_t, c_void_p
from ctypes.wintypes import \
    HANDLE, DWORD, HWND, BOOL, INT, UINT, \
    LONG, ULONG, LPWSTR, LPCWSTR, \
    LPVOID, LPCVOID, LPARAM, PULONG, \
    PDWORD, HMODULE

from module.device.platform.winapi.structures_windows import \
    SECURITY_ATTRIBUTES, STARTUPINFOW, WINDOWPLACEMENT, \
    PROCESS_INFORMATION, PROCESSENTRY32W, THREADENTRY32, \
    FILETIME, MSGBOXPARAMSW
from module.logger import logger

__all__ = [
    'user32', 'kernel32', 'ntdll', 'shell32',
    'IsUserAnAdmin', 'GetCurrentProcessId', 'CreateProcessW',
    'WaitForInputIdle', 'TerminateProcess', 'GetForegroundWindow',
    'SetForegroundWindow', 'GetWindowPlacement', 'SetWindowPlacement',
    'ShowWindow', 'GetWindow', 'EnumWindowsProc', 'EnumWindows',
    'GetWindowThreadProcessId', 'OpenProcess', 'OpenThread',
    'CreateToolhelp32Snapshot', 'CloseHandle', 'Process32First',
    'Process32Next', 'Thread32First', 'Thread32Next', 'GetProcessTimes',
    'GetThreadTimes', 'GetExitCodeProcess', 'GetLastError',
    'ReadProcessMemory', 'NtQueryInformationProcess', 'MessageBoxW',
    'MessageBoxIndirectW', 'GetModuleHandleW',
    'report', 'Handle_', 'ProcessHandle', 'ThreadHandle', 'CreateSnapshot',
    'open_process', 'open_thread', 'create_snapshot',
    'hex_or_normalize_path', 'get_callable_path'
]

user32      = WinDLL(name='user32',     use_last_error=True)
kernel32    = WinDLL(name='kernel32',   use_last_error=True)
ntdll       = WinDLL(name='ntdll',      use_last_error=True)
shell32     = WinDLL(name='shell32',    use_last_error=True)

IsUserAnAdmin                       = shell32.IsUserAnAdmin
IsUserAnAdmin.argtypes              = []
IsUserAnAdmin.restype               = BOOL

GetCurrentProcessId                 = kernel32.GetCurrentProcessId
GetCurrentProcessId.argtypes        = []
GetCurrentProcessId.restype         = DWORD

CreateProcessW                      = kernel32.CreateProcessW
CreateProcessW.argtypes             = [
    LPCWSTR,
    LPWSTR,
    POINTER(SECURITY_ATTRIBUTES),
    POINTER(SECURITY_ATTRIBUTES),
    BOOL,
    DWORD,
    LPVOID,
    LPCWSTR,
    POINTER(STARTUPINFOW),
    POINTER(PROCESS_INFORMATION)
]
CreateProcessW.restype              = BOOL

WaitForInputIdle                    = user32.WaitForInputIdle
WaitForInputIdle.argtypes           = [HANDLE, DWORD]
WaitForInputIdle.restype            = DWORD

TerminateProcess                    = kernel32.TerminateProcess
TerminateProcess.argtypes           = [HANDLE, UINT]
TerminateProcess.restype            = BOOL

GetForegroundWindow                 = user32.GetForegroundWindow
GetForegroundWindow.argtypes        = []
GetForegroundWindow.restype         = HWND
SetForegroundWindow                 = user32.SetForegroundWindow
SetForegroundWindow.argtypes        = [HWND]
SetForegroundWindow.restype         = BOOL

GetWindowPlacement                  = user32.GetWindowPlacement
GetWindowPlacement.argtypes         = [HWND, POINTER(WINDOWPLACEMENT)]
GetWindowPlacement.restype          = BOOL

SetWindowPlacement                  = user32.SetWindowPlacement
SetWindowPlacement.argtypes         = [HWND, POINTER(WINDOWPLACEMENT)]
SetWindowPlacement.restype          = BOOL

ShowWindow                          = user32.ShowWindow
ShowWindow.argtypes                 = [HWND, INT]
ShowWindow.restype                  = BOOL

GetWindow                           = user32.GetWindow
GetWindow.argtypes                  = [HWND, UINT]
GetWindow.restype                   = HWND

EnumWindowsProc                     = WINFUNCTYPE(BOOL, HWND, LPARAM, use_last_error=True)
EnumWindows                         = user32.EnumWindows
EnumWindows.argtypes                = [EnumWindowsProc, LPARAM]
EnumWindows.restype                 = BOOL
GetWindowThreadProcessId            = user32.GetWindowThreadProcessId
GetWindowThreadProcessId.argtypes   = [HWND, PDWORD]
GetWindowThreadProcessId.restype    = DWORD

OpenProcess                         = kernel32.OpenProcess
OpenProcess.argtypes                = [DWORD, BOOL, DWORD]
OpenProcess.restype                 = HANDLE
OpenThread                          = kernel32.OpenThread
OpenThread.argtypes                 = [DWORD, BOOL, DWORD]
OpenThread.restype                  = HANDLE

CreateToolhelp32Snapshot            = kernel32.CreateToolhelp32Snapshot
CreateToolhelp32Snapshot.argtypes   = [DWORD, DWORD]
CreateToolhelp32Snapshot.restype    = HANDLE

CloseHandle                         = kernel32.CloseHandle
CloseHandle.argtypes                = [HANDLE]
CloseHandle.restype                 = BOOL

Process32First                      = kernel32.Process32First
Process32First.argtypes             = [HANDLE, POINTER(PROCESSENTRY32W)]
Process32First.restype              = BOOL

Process32Next                       = kernel32.Process32Next
Process32Next.argtypes              = [HANDLE, POINTER(PROCESSENTRY32W)]
Process32Next.restype               = BOOL

Thread32First                       = kernel32.Thread32First
Thread32First.argtypes              = [HANDLE, POINTER(THREADENTRY32)]
Thread32First.restype               = BOOL

Thread32Next                        = kernel32.Thread32Next
Thread32Next.argtypes               = [HANDLE, POINTER(THREADENTRY32)]
Thread32Next.restype                = BOOL

GetProcessTimes                     = kernel32.GetProcessTimes
GetProcessTimes.argtypes            = [
    HANDLE,
    POINTER(FILETIME),
    POINTER(FILETIME),
    POINTER(FILETIME),
    POINTER(FILETIME)
]
GetProcessTimes.restype             = BOOL

GetThreadTimes                      = kernel32.GetThreadTimes
GetThreadTimes.argtypes             = [
    HANDLE,
    POINTER(FILETIME),
    POINTER(FILETIME),
    POINTER(FILETIME),
    POINTER(FILETIME)
]
GetThreadTimes.restype              = BOOL

GetExitCodeProcess                  = kernel32.GetExitCodeProcess
GetExitCodeProcess.argtypes         = [HANDLE, PDWORD]
GetExitCodeProcess.restype          = BOOL

GetLastError                        = kernel32.GetLastError
GetLastError.argtypes               = []
GetLastError.restype                = DWORD

SIZE_T                              = c_size_t
PSIZE_T                             = POINTER(SIZE_T)
NTSTATUS                            = LONG
ReadProcessMemory                   = kernel32.ReadProcessMemory
ReadProcessMemory.argtypes          = [HANDLE, LPCVOID, LPVOID, SIZE_T, PSIZE_T]
ReadProcessMemory.restype           = BOOL

NtQueryInformationProcess           = ntdll.NtQueryInformationProcess
NtQueryInformationProcess.argtypes  = [HANDLE, INT, LPVOID, ULONG, PULONG]
NtQueryInformationProcess.restype   = NTSTATUS

MessageBoxW                         = user32.MessageBoxW
MessageBoxW.argtypes                = [HWND, LPCWSTR, LPCWSTR, UINT]
MessageBoxW.restype                 = INT

MessageBoxIndirectW                 = user32.MessageBoxIndirectW
MessageBoxIndirectW.argtypes        = [POINTER(MSGBOXPARAMSW)]
MessageBoxIndirectW.restype         = INT

GetModuleHandleW                    = kernel32.GetModuleHandleW
GetModuleHandleW.argtypes           = [LPCWSTR]
GetModuleHandleW.restype            = HMODULE

def report(
        msg: str        = '',
        *args: tuple,
        r_status: bool  = True,
        status: int     = -1,
        use_log: bool   = True,
        level: int      = 40,
        r_exc: bool     = True,
        exc: type       = OSError,
        **kwargs: dict
) -> None:
    """
    Report any exception.

    Args:
        msg (str): The message to report.
        args (tuple): Additional arguments.
        r_status (bool): Whether to report the status code.
        status (int): The status code to report.
        use_log (bool): Whether to log the message.
        level (int): Logging level
        r_exc (bool): Flag indicating whether to raise an exception.
        exc (Type[Exception]): Exception class to raise.
        kwargs (dict): Additional keyword arguments.

    Raises:
        Optional[OSError]: The specified exception class if r_exc is True.
    """
    message: list = [msg]
    if r_status:
        if status == -1:
            status = GetLastError()
        message.append(f"Status code: 0x{status:08x}")
    if args:
        message.append(f"args: {' '.join(map(str, args))}")
    if kwargs:
        message.append(f"kwargs: {kwargs}")
    message: str = '. '.join(message)
    if use_log:
        logger.log(level, message)
    if r_exc:
        raise exc(message)

class Handle_(metaclass=ABCMeta):
    """
    Abstract base Handle class.
    Please override these functions if needed.
    """
    _handle:    Optional[c_void_p]
    _func:      Callable[..., c_void_p]
    _exitfunc:  Callable[[c_void_p], None]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if hasattr(self, '_func'):
            self._handle = HANDLE(self._func(*self.__get_init_args__(*args, **kwargs)))
            assert self, report(
                f"{self._func.__name__} failed",
                use_log=kwargs.get('use_log', True),
                r_exc=kwargs.get("r_exc", True)
            )

    def __enter__(self) -> HANDLE:
        return self._handle

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[BaseException], exc_tb: Optional[Any]):
        if self and hasattr(self, '_exitfunc'):
            self._exitfunc(self._handle)
            self._handle = None

    def __bool__(self) -> bool:
        return self._is_valid_handle()

    @abstractmethod
    def __get_init_args__(self, *args: Any, **kwargs: Any) -> tuple: ...

    def _is_valid_handle(self) -> bool:
        return self._handle.value is not None

class ProcessHandle(Handle_):
    """
    Process handle class.
    """
    _func       = OpenProcess
    _exitfunc   = CloseHandle

    def __get_init_args__(self, access: int, pid: int, use_log: bool, r_exc: bool) -> tuple:
        return access, False, pid

class ThreadHandle(Handle_):
    """
    Thread handle class.
    """
    _func       = OpenThread
    _exitfunc   = CloseHandle

    def __get_init_args__(self, access: int, tid: int, use_log: bool, r_exc: bool) -> tuple:
        return access, False, tid

class CreateSnapshot(Handle_):
    """
    Snapshot handle class.
    """
    _func       = CreateToolhelp32Snapshot
    _exitfunc   = CloseHandle

    def __get_init_args__(self, access, use_log: bool, r_exc: bool) -> tuple:
        return access, DWORD(0)

    def _is_invalid_handle(self) -> bool:
        from module.device.platform.winapi.const_windows import INVALID_HANDLE_VALUE
        return self._handle == INVALID_HANDLE_VALUE

def open_process(access: int, pid: int, use_log: bool = False, r_exc: bool = True) -> ProcessHandle:
    return ProcessHandle(access, pid, use_log=use_log, r_exc=r_exc)

def open_thread(access: int, tid: int, use_log: bool = False, r_exc: bool = True) -> ThreadHandle:
    return ThreadHandle(access, tid, use_log=use_log, r_exc=r_exc)

def create_snapshot(access: int, use_log: bool = False, r_exc: bool = True) -> CreateSnapshot:
    return CreateSnapshot(access, use_log=use_log, r_exc=r_exc)

def hex_or_normalize_path(input_str: str) -> Union[int, str]:
    """
    Args:
        input_str (str): The input string.

    Returns:
        Union[int, str]: The input string as an integer if it is a valid hex number,
            otherwise the input string with backslashes replaced with forward slashes and double quotes removed.
    """
    try:
        return int(input_str, 16)
    except ValueError:
        return input_str.replace(r"\\", "/").replace("\\", "/").replace('\"', '"')

def get_callable_path(_callable: Callable[..., Any]) -> str:
    """
    Get the relative path of a callable.

    Args:
        _callable (Callable[..., Any]):

    Examples:
        >>> get_callable_path(report)
        'module.device.platform.winapi.functions_windows.report'
        >>> get_callable_path(FILETIME.__init_subclass__)
        'module.device.platform.winapi.structures_windows.Structure::__init_subclass__'
        >>> get_callable_path(lambda x: x)
        '__main__.<lambda>'


    Returns:
        str: Functions's relative path.
    """
    if not callable(_callable):
        raise TypeError(f"Expected a callable, but got `{type(_callable).__name__}`")

    module = getattr(_callable, '__module__', '')
    qualname = getattr(_callable, '__qualname__', getattr(_callable, '__name__', '')).replace('.', '::')

    return '.'.join(filter(lambda x: x != '', [module, qualname]))
