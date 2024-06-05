@rem
@echo off

set "_root=%~dp0"
set "_root=%_root:~0,-1%"
%~d0
cd "%_root%"

color F0

set "_pyBin=%_root%\toolkit"
set "_GitBin=%_root%\toolkit\Git\mingw64\bin"
set "_adbBin=%_root%\toolkit\Lib\site-packages\adbutils\binaries"
set "PATH=%_root%\toolkit\alias;%_root%\toolkit\command;%_pyBin%;%_pyBin%\Scripts;%_GitBin%;%_adbBin%;%PATH%"
set "ELECTRON_ENABLE_LOGGING=1"

title Alas Console Debugger
echo This is an console to run adb, git, python and pip.
echo     adb devices
echo     git log
echo     python -V
echo     pip -V
echo. & echo ----- & echo.
echo.
)
echo.

PROMPT $P$_$G$G$G
cmd /Q /K
