@rem
:: Used for "Alas-Deploy-Tool-V4.bat" in :Create_Console-bat
:: Please make sure that: only call this batch when %cd% is %root%;
:: e.g.
:: call command\GenerateConsoleBatch.bat portable

@echo off
set "console-bat-filename=console.bat"
REM if "%DeployMode%"=="unknown" exit
call :GenerateConsoleBatch_Common
call :GenerateConsoleBatch-%~1
call :GenerateConsoleBatch_Common2
goto :eof


rem ================= FUNCTIONS =================


:GenerateConsoleBatch_Common
( echo @rem
echo @echo off
echo.

REM :: Set the root directory
echo set "_root=%%~dp0"
echo set "_root=%%_root:~0,-1%%"
echo cd "%%_root%%"
echo.

REM :: Set the color scheme
echo color F0
echo.

echo if exist %root%\config\deploy.ini ^(
echo     for /f "tokens=3 delims= " %%%%i in ^('findstr /i "Proxy" %root%\config\deploy.ini'^) do ^( set "_state_globalProxy=%%%%i" ^)
echo     for /f "tokens=3 delims= " %%%%i in ^('findstr /i "ProxyHost" %root%\config\deploy.ini'^) do ^( set "__proxyHost=%%%%i" ^)
echo     for /f "tokens=3 delims= " %%%%i in ^('findstr /i "HttpPort" %root%\config\deploy.ini'^) do ^( set "__httpPort=%%%%i" ^)
echo     for /f "tokens=3 delims= " %%%%i in ^('findstr /i "HttpsPort" %root%\config\deploy.ini'^) do ^( set "__httpsPort=%%%%i" ^)
echo ^)
echo.

REM :: Set the environment variables %PATH%
echo set "_pyBin=%%_root%%\toolkit"
echo set "_GitBin=%%_root%%\toolkit\Git\mingw64\bin"
echo set "_adbBin=%%_root%%\toolkit\Lib\site-packages\adbutils\binaries"
echo set "PATH=%%_root%%\toolkit\alias;%%_root%%\toolkit\command;%%_pyBin%%;%%_pyBin%%\Scripts;%%_GitBin%%;%%_adbBin%%;%%PATH%%"
echo.

echo if NOT exist toolkit\command md toolkit\command
echo del /Q toolkit\command\*.cmd ^>NUL 2^>NUL) > %console-bat-filename%
goto :eof

:GenerateConsoleBatch_Common2
( REM :: Show the instructions
echo title Alas Console Debugger
echo echo This is an console to run adb, git, python and pip.
echo echo     adb devices
echo echo     git log
echo echo     python -V
echo echo     pip -V
echo echo. ^& echo ----- ^& echo.
echo echo.
echo ^)

echo echo.
echo.
REM :: To custom the style, get usage by `help prompt`. Such as:
REM :: PROMPT [$D $T$h$h$h$h$h$h]$_$P$_$G$G$G
echo PROMPT $P$_$G$G$G
echo cmd /Q /K) >> %console-bat-filename%
goto :eof

:GenerateConsoleBatch-New
( echo echo @"%%_pyBin%%\python.exe" "%%_pyBin%%\Scripts\pip3.exe" %%%%*^> toolkit\command\pip3.cmd
echo echo @"%%_pyBin%%\python.exe" "%%_pyBin%%\Scripts\pip.exe" %%%%*^> toolkit\command\pip.cmd
echo echo @"%%_pyBin%%\python.exe" "%%_pyBin%%\Scripts\wheel.exe" %%%%*^> toolkit\command\wheel.cmd
echo echo @"%%_pyBin%%\python.exe" "%%_pyBin%%\Scripts\easy_install.exe" %%%%*^> toolkit\command\easy_install.cmd) >> %console-bat-filename%
goto :eof

rem ================= End of File =================
