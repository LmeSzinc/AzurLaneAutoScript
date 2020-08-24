@rem
:: Used for "ADT-V4.bat" in =Preparation=
:: Pay attention to %cd% limit according to each Function.
:: e.g.
:: call command\Get.bat Proxy
:: call command\Get.bat InfoOpt6
:: call command\Get.bat DeployMode
:: call command\Get.bat WgetOptions

@echo off
call :Import_%~1
goto :eof

rem ================= FUNCTIONS =================

:Import_Deploy

:: %cd%: "%root%"
:: Get %Language% , %Region% , %SystemType%
:Import_Main
:: 1. Get customized %Language%, or decided by "LanguageSelector"
call command\SystemSet.bat
call command\LanguageSet.bat
if exist config\alas.ini (
    for /f "tokens=3 delims= " %%i in ('findstr /i "github_token" config\alas.ini') do ( set "GithubToken=%%i" )
    for /f "tokens=3 delims= " %%i in ('findstr /i "serial" config\alas.ini') do ( set "SerialAlas=%%i" )
)
if exist config\template.ini (
    for /f "tokens=3 delims= " %%i in ('findstr /i "serial" config\template.ini') do ( set "SerialTemplate=%%i" )
)
if exist config\deploy.ini (
    for /f "tokens=3 delims= " %%i in ('findstr /i "Language" config\deploy.ini') do ( set "Language=%%i" )
    for /f "tokens=3 delims= " %%i in ('findstr /i "Region" config\deploy.ini') do ( set "Region=%%i" )
    for /f "tokens=3 delims= " %%i in ('findstr /i "SystemType" config\deploy.ini') do ( set "SystemType=%%i" )
    for /f "tokens=3 delims= " %%i in ('findstr /i "FirstRun" config\deploy.ini') do ( set "FirstRun=%%i" )
    for /f "tokens=3 delims= " %%i in ('findstr /i "IsUsingGit" config\deploy.ini') do ( set "IsUsingGit=%%i" )
    for /f "tokens=3 delims= " %%i in ('findstr /i "KeepLocalChanges" config\deploy.ini') do ( set "KeepLocalChanges=%%i" )
    for /f "tokens=3 delims= " %%i in ('findstr /i "RealtimeMode" config\deploy.ini') do ( set "RealtimeMode=%%i" )
    for /f "tokens=3 delims= " %%i in ('findstr /i "Branch" config\deploy.ini') do ( set "Branch=%%i" )
    for /f "tokens=3 delims= " %%i in ('findstr /i "AdbConnect" config\deploy.ini') do ( set "AdbConnect=%%i" )
    for /f "tokens=3 delims= " %%i in ('findstr /i "Serial" config\deploy.ini') do ( set "Serial=%%i" )
    for /f "tokens=3 delims= " %%i in ('findstr /i "AdbKillServer" config\deploy.ini') do ( set "KillServer=%%i" )
) else (
    call command\LanguageSet.bat
    )

:: 2. Get %SystemType% by "SystemTypeSelector"
:: 3. Overwrite the default %Region% and %SystemType% if customized
rem if exist config\deploy.ini (
rem     for /f "tokens=3 delims= " %%i in ('findstr /i "Region" config\deploy.ini') do ( set "Region=%%i" )
rem     for /f "tokens=3 delims= " %%i in ('findstr /i "SystemType" config\deploy.ini') do ( set "SystemType=%%i" )
rem     for /f "tokens=3 delims= " %%i in ('findstr /i "FirstRun" config\deploy.ini') do ( set "FirstRun=%%i" )
rem     for /f "tokens=3 delims= " %%i in ('findstr /i "IsUsingGit" config\deploy.ini') do ( set "IsUsingGit=%%i" )
rem )
rem if exist config\deploy.ini (
rem     for /f "tokens=3 delims= " %%i in ('findstr /i "KeepLocalChanges" config\deploy.ini') do ( set "KeepLocalChanges=%%i" )
rem     for /f "tokens=3 delims= " %%i in ('findstr /i "RealtimeMode" config\deploy.ini') do ( set "RealtimeMode=%%i" )
rem     for /f "tokens=3 delims= " %%i in ('findstr /i "Branch" config\deploy.ini') do ( set "Branch=%%i" )
rem     for /f "tokens=3 delims= " %%i in ('findstr /i "Serial" config\deploy.ini') do ( set "Serial=%%i" )
rem )
goto :eof

:Import_Serial
if "%FirstRun%"=="no" goto :eof
echo ====================================================================================================
echo Enter your HOST:PORT eg: 127.0.0.1:5555
echo If you misstype, you can set in Settings menu Option 3
echo ====================================================================================================
set /p serial_input=Please input - SERIAL ^(DEFAULT 127.0.0.1:5555 ^): 
if "%serial_input%"=="" ( set "serial_input=127.0.0.1:5555" )
%adbBin% kill-server > nul 2>&1
%adbBin% connect %serial_input% | find /i "connected to" >nul
echo ====================================================================================================
if errorlevel 1 (
    echo The connection was not successful on SERIAL: %Serial%
    echo Check our wiki for more info
    pause > NUL
    start https://github.com/LmeSzinc/AzurLaneAutoScript/wiki/Installation_en
    goto Import_Serial
) else (
    call command\Config.bat Serial %serial_input%
    call command\ConfigTemplate.bat SerialTemplate %serial_input%
    %pyBin% -m uiautomator2 init
    echo The connection was Successful on SERIAL: %Serial%
)
echo ====================================================================================================
echo Old Serial:      %Serial%
echo New Serial:      %serial_input% 
echo ====================================================================================================
echo Press any to continue...
pause > NUL
goto :eof


:: %cd%: "%root%"
:: Get the proxy settings of CMD from "config\deploy.ini"
:Import_Proxy
if exist config\deploy.ini (
    for /f "tokens=3 delims= " %%i in ('findstr /i "Proxy" config\deploy.ini') do ( set "state_globalProxy=%%i" )
    for /f "tokens=3 delims= " %%i in ('findstr /i "ProxyHost" config\deploy.ini') do ( set "__proxyHost=%%i" )
    for /f "tokens=3 delims= " %%i in ('findstr /i "HttpPort" config\deploy.ini') do ( set "__httpPort=%%i" )
    for /f "tokens=3 delims= " %%i in ('findstr /i "HttpsPort" config\deploy.ini') do ( set "__httpsPort=%%i" )
) else ( set "state_globalProxy=disable" )
goto :eof

:: Get %DeployMode% from "deploy.log"
:Import_DeployMode
if exist deploy.log (
    for /f "tokens=2 delims= " %%i in ('findstr /i "DeployMode" deploy.log') do ( set "DeployMode=%%i" )
) else ( set "DeployMode=unknown" )
goto :eof

:: %cd%: "%root%"
:: Get %opt3_info% according to "deploy.log"
:Import_InfoOpt3
set "opt3_info="
if exist deploy.log (
    pushd toolkit && call :Import_DeployMode && popd
    if "!DeployMode!"=="New" set "opt3_info=(New)"
    if "!DeployMode!"=="Legacy" set "opt3_info=(Legacy)"
)
goto :eof

:: %cd%: "%root%"
:: Get %opt4_info% according to "Console.bat"
:Import_InfoOpt4
set "opt4_info="
if exist console.bat (
    for /f "tokens=2 delims==" %%i in ('findstr /i "_versionAtCreation=" console.bat') do ( set "_versionAtCreation=%%~i" )
    set "_versionAtCreation=!_versionAtCreation:~0,-1!"
    REM If "_versionAtCreation" is not found, "%_versionAtCreation%" will be "~0,-1".  Next statement will still be executed.
    if NOT "!_versionAtCreation!"=="%Version%" ( set "opt4_info=^>^>^>Perform this action after update^<^<^<" )
)
goto :eof

:: %cd%: No limit
:: Get %opt6_info% according to :Import_GlobalProxy ; Apply the proxy settings if Proxy is enabled.
:: call :Import_Proxy before calling this function.
:Import_InfoOpt6
if "%state_globalProxy%"=="enable" (
    set "http_proxy=%__proxyHost%:%__httpPort%"
    set "https_proxy=%__proxyHost%:%__httpsPort%"
    set "opt6_info=(Global Proxy: enabled)"
) else ( set "opt6_info=" )
goto :eof

rem ================= End of File =================
