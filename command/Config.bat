@rem
:: Used for "ADT-V4.bat" in :setting_Proxy
:: Please make sure that: only call this batch when %cd% is %root%;
:: e.g.
:: call command\Config.bat Language zh
:: call command\Config.bat Region origin
:: call command\Config.bat SystemType
:: call command\Config.bat ProxyHost http://127.0.0.1

@echo off
setlocal EnableDelayedExpansion
set "cfg_File=%root%\config\deploy.ini"
set "cfg_Alas=%root%\config\alas.ini"
set "cfg_Extra=%~2"
call :Config_Common
call :Config_%~1
call :Config_Common2
goto :eof

rem ================= FUNCTIONS =================

:Config_Common
cd toolkit
if NOT exist %cfg_File% (
    REM Set to default
    ( echo Language = %Language%
    echo Region = %Region%
    echo SystemType = %SystemType%
    echo NetTest = enable
    echo KeepLocalChanges = disable
    echo RealtimeMode = disable
    echo AdbConnect = enable
    echo Serial = %Serial%
    echo FirstRun = %FirstRun%
    echo IsUsingGit = %IsUsingGit%
    echo Branch = master
    echo ProxyGlobal = disable
    echo ProxyHost = http://127.0.0.1
    echo HttpPort = 1080
    echo HttpsPort = 1080)> %cfg_File%
)
copy %cfg_File% %cfg_File%.bak > NUL
type NUL > %cfg_File%
goto :eof


:Config_Common2
del /Q %cfg_File%.bak >NUL 2>NUL
cd ..
goto :eof


:: There are 3 types of configuration items: assignable, toggle-able, or both.
::     Assignable : You should call it with an argument `%2`.
::     Toggle-able: No argument `%2`. If it is already enabled, set it to disabled and vice versa.
::     Both       : If you call it without argument `%2`, toggle it. Otherwise assign it.

:: Toggle-able: SystemType, ProxyHint, FFmpeg, NetTest, UpgradeOnlyViaGitHub
:: Assignable : Language, Region, ProxyHost, HttpPort, HttpsPort
:: Both       : Proxy

:Config_Region
for /f "delims=" %%i in (%cfg_File%.bak) do (
    set "cfg_Content=%%i"
    echo %%i | findstr "Region" >NUL && ( set "cfg_Content=Region = %cfg_Extra%" )
    echo !cfg_Content!>>%cfg_File%
)
echo Download Region has been set to:%cfg_Extra%
echo Please re-run this batch to make the settings take effect.
goto :eof

:Config_SystemType
for /f "delims=" %%i in (%cfg_File%.bak) do (
    set "cfg_Temp=%%i"
    set "cfg_Content=!cfg_Temp!"
    if "!cfg_Temp!"=="SystemType = 64" ( set "cfg_Content=SystemType = 32" && set "cfg_State=32" )
    if "!cfg_Temp!"=="SystemType = 32" ( set "cfg_Content=SystemType = 64" && set "cfg_State=64" )
    echo !cfg_Content!>>%cfg_File%
)
if "%cfg_State%"=="32" (
    echo System Type has been set to: 32bit
) else echo System Type has been set to: 64bit
goto :eof

:: call command\Config.bat Proxy ==> Toggle enabled/disabled
:: call command\Config.bat Proxy enable ==> Enable it
:: call command\Config.bat Proxy disable ==> Disable it
:Config_Proxy
if "%cfg_Extra%"=="" (
    for /f "delims=" %%i in (%cfg_File%.bak) do (
        set "cfg_Temp=%%i"
        set "cfg_Content=!cfg_Temp!"
        if "!cfg_Temp!"=="ProxyGlobal = disable" ( set "cfg_Content=ProxyGlobal = enable" && set "cfg_State=enable" )
        if "!cfg_Temp!"=="ProxyGlobal = enable" ( set "cfg_Content=ProxyGlobal = disable" && set "cfg_State=disable" )
        echo !cfg_Content!>>%cfg_File%
    )
) else (
    for /f "delims=" %%i in (%cfg_File%.bak) do (
        set "cfg_Content=%%i"
        echo %%i | findstr "ProxyGlobal" >NUL && ( set "cfg_Content=ProxyGlobal = %cfg_Extra%" )
        echo !cfg_Content!>>%cfg_File%
    )
    set "cfg_State=%cfg_Extra%"
)
if "%cfg_State%"=="enable" (
    echo Global Proxy: enabled
) else echo Global Proxy: disabled ^(DEFAULT^)
goto :eof

:Config_ProxyHost
for /f "delims=" %%i in (%cfg_File%.bak) do (
    set "cfg_Content=%%i"
    echo %%i | findstr "ProxyHost" >NUL && ( set "cfg_Content=ProxyHost = %cfg_Extra%" )
    echo !cfg_Content!>>%cfg_File%
)
goto :eof

:Config_HttpPort
for /f "delims=" %%i in (%cfg_File%.bak) do (
    set "cfg_Content=%%i"
    echo %%i | findstr "HttpPort" >NUL && ( set "cfg_Content=HttpPort = %cfg_Extra%" )
    echo !cfg_Content!>>%cfg_File%
)
goto :eof

:Config_HttpsPort
for /f "delims=" %%i in (%cfg_File%.bak) do (
    set "cfg_Content=%%i"
    echo %%i | findstr "HttpsPort" >NUL && ( set "cfg_Content=HttpsPort = %cfg_Extra%" )
    echo !cfg_Content!>>%cfg_File%
)
goto :eof

:Config_NetTest
for /f "delims=" %%i in (%cfg_File%.bak) do (
    set "cfg_Temp=%%i"
    set "cfg_Content=!cfg_Temp!"
    if "!cfg_Temp!"=="NetTest = disable" ( set "cfg_Content=NetTest = enable" && set "cfg_State=enable" )
    if "!cfg_Temp!"=="NetTest = enable" ( set "cfg_Content=NetTest = disable" && set "cfg_State=disable" )
    echo !cfg_Content!>>%cfg_File%
)
if "%cfg_State%"=="enable" (
    echo Network connection test while upgrading: enabled ^(DEFAULT^)
) else echo Network connection test while upgrading: disabled
goto :eof

:Config_IsUsingGit
for /f "delims=" %%i in (%cfg_File%.bak) do (
    set "cfg_Content=%%i"
    echo %%i | findstr "IsUsingGit" >NUL && ( set "cfg_Content=IsUsingGit = %IsUsingGit%" )
    echo !cfg_Content!>>%cfg_File%
)
goto :eof

:Config_FirstRun
for /f "delims=" %%i in (%cfg_File%.bak) do (
    set "cfg_Content=%%i"
    echo %%i | findstr "FirstRun" >NUL && ( set "cfg_Content=FirstRun = %FirstRun%" )
    echo !cfg_Content!>>%cfg_File%
)
goto :eof

:Config_KeepLocalChanges
for /f "delims=" %%i in (%cfg_File%.bak) do (
    set "cfg_Temp=%%i"
    set "cfg_Content=!cfg_Temp!"
    if "!cfg_Temp!"=="KeepLocalChanges = disable" ( set "cfg_Content=KeepLocalChanges = enable" && set "cfg_State=enable" )
    if "!cfg_Temp!"=="KeepLocalChanges = enable" ( set "cfg_Content=KeepLocalChanges = disable" && set "cfg_State=disable" )
    echo !cfg_Content!>>%cfg_File%
)
if "%cfg_State%"=="disable" (
    echo Keep local changes when updating: Disable ^(DEFAULT^)
) else echo Keep local changes when updating: Enable
goto :eof

:Config_Branch
for /f "delims=" %%i in (%cfg_File%.bak) do (
    set "cfg_Temp=%%i"
    set "cfg_Content=!cfg_Temp!"
    if "!cfg_Temp!"=="Branch = master" ( set "cfg_Content=Branch = dev" && set "cfg_State=dev" )
    if "!cfg_Temp!"=="Branch = dev" ( set "cfg_Content=Branch = master" && set "cfg_State=master" )
    echo !cfg_Content!>>%cfg_File%
)
if "%cfg_State%"=="master" (
    echo Branch: Master ^(DEFAULT^)
) else echo Branch: Dev
goto :eof

:Config_RealtimeMode
for /f "delims=" %%i in (%cfg_File%.bak) do (
    set "cfg_Temp=%%i"
    set "cfg_Content=!cfg_Temp!"
    if "!cfg_Temp!"=="RealtimeMode = disable" ( set "cfg_Content=RealtimeMode = enable" && set "cfg_State=enable" )
    if "!cfg_Temp!"=="RealtimeMode = enable" ( set "cfg_Content=RealtimeMode = disable" && set "cfg_State=disable" )
    echo !cfg_Content!>>%cfg_File%
)
if "%cfg_State%"=="disable" (
    echo Bluestacks Beta realtime connection mode: Disable ^(DEFAULT^)
) else echo Bluestacks Beta realtime connection mode: Enable
goto :eof

:Config_Serial
for /f "delims=" %%i in (%cfg_File%.bak) do (
    set "cfg_Content=%%i"
    echo %%i | findstr "Serial" >NUL && ( set "cfg_Content=Serial = %cfg_Extra%" )
    echo !cfg_Content!>>%cfg_File%
)
goto :eof

:Config_UpgradeOnlyViaGitHub
for /f "delims=" %%i in (%cfg_File%.bak) do (
    set "cfg_Temp=%%i"
    set "cfg_Content=!cfg_Temp!"
    if "!cfg_Temp!"=="UpgradeOnlyViaGitHub = disable" ( set "cfg_Content=UpgradeOnlyViaGitHub = enable" && set "cfg_State=enable" )
    if "!cfg_Temp!"=="UpgradeOnlyViaGitHub = enable" ( set "cfg_Content=UpgradeOnlyViaGitHub = disable" && set "cfg_State=disable" )
    echo !cfg_Content!>>%cfg_File%
)
if "%cfg_State%"=="enable" (
    echo Upgrade you-get via: GitHub_Releases
) else echo Upgrade you-get via: PyPI.org ^(DEFAULT^)
goto :eof

rem ================= End of File =================
