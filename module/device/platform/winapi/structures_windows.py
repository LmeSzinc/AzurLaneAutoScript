from re import search, fullmatch

from ctypes import \
    POINTER, Structure as _Structure, WINFUNCTYPE, \
    c_int32, c_uint32, c_uint64, c_uint16, \
    c_wchar, c_wchar_p, c_void_p, c_ubyte, c_byte, c_long, c_ulong
from ctypes.wintypes import MAX_PATH, FILETIME as _FILETIME

__all__ = [
    'WinApiBaseException', 'EmulatorLaunchFailedError', 'HwndNotFoundError', 'IterationFinished',
    'Structure', 'PROCESS_INFORMATION', 'STARTUPINFOW', 'SECURITY_ATTRIBUTES',
    'PROCESSENTRY32W', 'THREADENTRY32', 'POINT', 'RECT', 'WINDOWPLACEMENT',
    'UNICODE_STRING', 'RTL_USER_PROCESS_PARAMETERS', 'PEB', 'PROCESS_BASIC_INFORMATION',
    'FILETIME', 'TIMEINFO', 'HELPINFO', 'LPHELPINFO', 'MSGBOXCALLBACK', 'MSGBOXPARAMSW'
]

class WinApiBaseException(Exception): ...

class EmulatorLaunchFailedError(WinApiBaseException): ...
class HwndNotFoundError(WinApiBaseException): ...
class IterationFinished(WinApiBaseException): ...

class Structure(_Structure):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.field_name, cls.field_type = zip(*cls._fields_)

    def __eq__(self, other):
        def eq_obj(x, y, *objs):
            return any(isinstance(x, obj) and isinstance(y, obj) and x == y for obj in objs)
        def eq_ptr(x, y):
            try:
                return x.contents.value == y.contents.value
            except AttributeError:
                return x.contents == y.contents
            except ValueError:
                return True

        if not isinstance(other, self.__class__):
            return NotImplemented

        for name, _type in self._fields_:
            vself, vother = getattr(self, name), getattr(other, name)
            if eq_obj(vself, vother, int, str, Structure):
                continue
            elif vself is None and vother is None:
                continue
            elif eq_ptr(vself, vother):
                continue
            match = search(r'\d+$', _type.__name__)
            if match is None:
                return False
            if all(vself[i] == vother[i] for i in range(int(match.group()))):
                continue
            else:
                return False
        return True

    def __bool__(self):
        def bool_obj(v, *objs):
            if isinstance(v, str):
                return v != '\x00'
            return isinstance(v, objs) and bool(v)
        def bool_ptr(val):
            try:
                return bool(val.contents.value)
            except AttributeError:
                return bool(val.contents)
            except ValueError:
                return False

        for name, _type in self._fields_:
            value = getattr(self, name)
            if bool_obj(value, int, Structure):
                return True
            if value is None:
                continue
            if bool_ptr(value):
                return True
            match = search(r'\d+$', _type.__name__)
            if match is None:
                continue
            if any(value[i] for i in range(int(match.group()))):
                return True
            else:
                continue
        return False

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            indices = range(*key.indices(len(self)))
            if len(indices) != len(value):
                raise ValueError("Value list length does not match slice length")
            for i, val in zip(indices, value):
                setattr(self, self.field_name[i], val)
        elif isinstance(key, int):
            if key < 0:
                key += len(self)
            if key < 0 or key >= len(self):
                raise IndexError("Index out of range")
            setattr(self, self.field_name[key], value)
        elif isinstance(key, str):
            if key not in self.field_name:
                raise KeyError(f"'{self.__class__.__name__}' object has no key '{key}'")
            setattr(self, key, value)
        else:
            raise TypeError("Invalid argument type")

    def __getitem__(self, item):
        if isinstance(item, slice):
            indices = range(*item.indices(len(self)))
            return [getattr(self, self.field_name[i]) for i in indices]
        elif isinstance(item, int):
            if item < 0:
                item += len(self)
            if item < 0 or item >= len(self):
                raise IndexError("Index out of range")
            return getattr(self, self.field_name[item])
        elif isinstance(item, str):
            if item not in self.field_name:
                raise KeyError(f"'{self.__class__.__name__}' object has no item '{item}'")
            return getattr(self, item)
        else:
            raise TypeError("Invalid argument type")

    def __format__(self, format_spec):
        def format_fields(spec, fix):
            values = [getattr(self, name) for name in self.field_name]
            return ', '.join(
                f"{name}={fix}" + f"{value:{spec}}".upper()
                if isinstance(value, int) else f"{name}={value}"
                for name, value in zip(self.field_name, values)
            )

        if format_spec == '':
            return str(self)
        if fullmatch(r'^\d*[bBxX]$', format_spec):
            prefix = '0b' if format_spec[-1] in 'bB' else '0x'
            return f"{self.__class__.__name__}({format_fields(format_spec, prefix)})"
        else:
            raise ValueError(f"Unsupported format specifier: {format_spec}")

    def __len__(self):
        return len(self.field_name)

    def __dir__(self):
        return [attr for attr in super().__dir__() if not attr.startswith('_')]

    def __repr__(self):
        field_values = ', '.join(f"{name}={getattr(self, name)!r}" for name in self.field_name)
        return f"{self.__class__.__name__}<{field_values}>"

    def __str__(self):
        field_values = ', '.join(f"{name}={getattr(self, name)}" for name in self.field_name)
        return f"{self.__class__.__name__}({field_values})"

    def __iter__(self):
        for name in self.field_name:
            yield name, getattr(self, name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb): ...

# processthreadsapi.h line 28
class PROCESS_INFORMATION(Structure):
    _fields_ = [
        ('hProcess',    c_void_p),
        ('hThread',     c_void_p),
        ('dwProcessId', c_uint32),
        ('dwThreadId',  c_uint32)
    ]

class STARTUPINFOW(Structure):
    _fields_ = [
        ("cb",              c_uint32),
        ("lpReserved",      POINTER(c_wchar)),
        ("lpDesktop",       POINTER(c_wchar)),
        ("lpTitle",         POINTER(c_wchar)),
        ("dwX",             c_uint32),
        ("dwY",             c_uint32),
        ("dwXSize",         c_uint32),
        ("dwYSize",         c_uint32),
        ("dwXCountChars",   c_uint32),
        ("dwYCountChars",   c_uint32),
        ("dwFillAttribute", c_uint32),
        ("dwFlags",         c_uint32),
        ("wShowWindow",     c_uint16),
        ("cbReserved2",     c_uint16),
        ("lpReserved2",     POINTER(c_ubyte)),
        ("hStdInput",       c_void_p),
        ("hStdOutput",      c_void_p),
        ("hStdError",       c_void_p)
    ]

# minwinbase.h line 13
class SECURITY_ATTRIBUTES(Structure):
    _fields_ = [
        ("nLength",                 c_uint32),
        ("lpSecurityDescriptor",    c_void_p),
        ("bInheritHandle",          c_int32)
    ]

# tlhelp32.h line 62
class PROCESSENTRY32W(Structure):
    _fields_ = [
        ("dwSize",              c_ulong),
        ("cntUsage",            c_ulong),
        ("th32ProcessID",       c_ulong),
        ("th32DefaultHeapID",   c_uint64),
        ("th32ModuleID",        c_ulong),
        ("cntThreads",          c_ulong),
        ("th32ParentProcessID", c_ulong),
        ("pcPriClassBase",      c_long),
        ("dwFlags",             c_ulong),
        ("szExeFile",           c_wchar * MAX_PATH)
    ]

class THREADENTRY32(Structure):
    _fields_ = [
        ("dwSize",              c_ulong),
        ("cntUsage",            c_ulong),
        ("th32ThreadID",        c_ulong),
        ("th32OwnerProcessID",  c_ulong),
        ("tpBasePri",           c_long),
        ("tpDeltaPri",          c_long),
        ("dwFlags",             c_ulong)
    ]

class POINT(Structure):
    _fields_ = [
        ("x", c_long),
        ("y", c_long)
    ]

class RECT(Structure):
    _fields_ = [
        ("left",    c_long),
        ("top",     c_long),
        ("right",   c_long),
        ("bottom",  c_long)
    ]

# winuser.h line 1801
class WINDOWPLACEMENT(Structure):
    _fields_ = [
        ("length",              c_uint32),
        ("flags",               c_uint32),
        ("showCmd",             c_uint32),
        ("ptMinPosition",       POINT),
        ("ptMaxPosition",       POINT),
        ("rcNormalPosition",    RECT),
        ("rcDevice",            RECT)
    ]

# winternl.h line 25
class UNICODE_STRING(Structure):
    _fields_ = [
        ("Length",          c_uint16),
        ("MaximumLength",   c_uint16),
        ("Buffer",          POINTER(c_wchar))
    ]

# winternl.h line 54
class RTL_USER_PROCESS_PARAMETERS(Structure):
    _fields_ = [
        ("Reserved",        c_byte * 96),
        ("ImagePathName",   UNICODE_STRING),
        ("CommandLine",     UNICODE_STRING)
    ]

class PEB(Structure):
    _fields_ = [
        ("Reserved1",           c_byte * 32),
        ("ProcessParameters",   POINTER(RTL_USER_PROCESS_PARAMETERS)),
    ]

class PROCESS_BASIC_INFORMATION(Structure):
    _fields_ = [
        ("ExitStatus",                      c_int32),
        ("PebBaseAddress",                  POINTER(PEB)),
        ("AffinityMask",                    c_uint64),
        ("BasePriority",                    c_int32),
        ("UniqueProcessId",                 c_uint64),
        ("InheritedFromUniqueProcessId",    c_uint64),
    ]

class FILETIME(Structure, _FILETIME):
    def to_int(self):
        return (self.dwHighDateTime << 32) + self.dwLowDateTime

class TIMEINFO(Structure):
    _fields_ = [
        ("CreationTime",    FILETIME),
        ("ExitTime",        FILETIME),
        ("KernelTime",      FILETIME),
        ("UserTime",        FILETIME)
    ]

class HELPINFO(Structure):
    _fields_ = [
        ("cbSize",          c_uint32),
        ("iContextType",    c_int32),
        ("iCtrlId",         c_int32),
        ("hItemHandle",     c_void_p),
        ("dwContextId",     c_uint32),
        ("MousePos",        POINT),
    ]

LPHELPINFO = POINTER(HELPINFO)
MSGBOXCALLBACK = WINFUNCTYPE(None, LPHELPINFO)

class MSGBOXPARAMSW(Structure):
    _fields_ = [
        ("cbSize",              c_uint32),
        ("hwndOwner",           c_void_p),
        ("hInstance",           c_void_p),
        ("lpszText",            c_wchar_p),
        ("lpszCaption",         c_wchar_p),
        ("dwStyle",             c_ulong),
        ("lpszIcon",            c_wchar_p),
        ("dwContextHelpId",     c_uint32),
        ("lpfnMsgBoxCallback",  MSGBOXCALLBACK),
        ("dwLanguageId",        c_ulong),
    ]
