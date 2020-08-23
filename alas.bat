@rem
:: Alas Run Tool v3
:: Author: whoamikyo (https://kyo.ninja)
:: Version: 3.0
:: Last updated: 2020-08-22
:: >>> Get updated from: https://github.com/LmeSzinc/AzurLaneAutoScript <<<
@echo off
pushd "%~dp0"
setlocal EnableDelayedExpansion
set "Version=3.0"
set "lastUpdated=2020-08-22"
:: Remote repo
set "Remoterepo=https://raw.githubusercontent.com/LmeSzinc/AzurLaneAutoScript/master/toolkit"

rem ================= Preparation =================

:: Set the root directory
set "root=%~dp0"
set "root=%root:~0,-1%"
cd "%root%"

:: Import main settings (%Language%, %Region%, %SystemType%) and translation text.
call command\Get.bat Main
:: Import the Proxy setting and apply. Then show more info in Option6.
call command\Get.bat Serial
call command\Get.bat Proxy
call command\Get.bat InfoOpt6
:: If already deployed, show more info in Option3.
call command\Get.bat InfoOpt3
rem call command\Get.bat InfoOpt4
call command\Get.bat DeployMode

:: Start of Deployment
title Alas Run Tool V3
set "pyBin=%root%\toolkit\python.exe"
set "adbBin=%root%\toolkit\Lib\site-packages\adbutils\binaries\adb.exe"
set "gitBin=%root%\toolkit\Git\mingw64\bin\git.exe"
set "curlBin=%root%\toolkit\Git\mingw64\bin\curl.exe"
set "api_json=%root%\config\api_git.json"
set "AlasConfig=%root%\config\alas.ini"
set "template=%root%\config\template.ini"
set "gitFolder=%root%\.git"
if "%IsUsingGit%"=="yes" if "%DeployMode%"=="unknown" ( xcopy /Y toolkit\config .git\ > NUL )
call :UpdateChecker_Alas

rem ================= Menu =================

:MENU
cd "%root%"
cls
:: Uncomment to debug the configuration that imported from "config\deploy.ini"
rem echo Language: %Language% & echo Region: %Region% & echo SystemType: %SystemType%
rem echo http_proxy: %http_proxy% & echo https_proxy: %https_proxy%
echo DeployMode: %DeployMode%
rem echo KeepLocalChanges: %KeepLocalChanges%
rem echo RealtimeMode: %RealtimeMode%
rem echo FirstRun: %FirstRun%
rem echo IsUsingGit: %IsUsingGit%
rem echo Serial: %Serial%
setLocal EnableDelayedExpansion
set "STR=Alas Run Tool %Version%^"
set "SIZE=100"
set "LEN=0"
:strLen_Loop
   if not "!!STR:~%LEN%!!"=="" set /A "LEN+=1" & goto :strLen_Loop
set "equal====================================================================================================="
set "spaces====================================================================================================="
call echo %%equal:~0,%SIZE%%%
set /a "pref_len=%SIZE%-%LEN%-2"
set /a "pref_len/=2"
set /a "suf_len=%SIZE%-%LEN%-2-%pref_len%"
call echo =%%spaces:~0,%pref_len%%%%%STR%%%%spaces:~0,%suf_len%%%=
call echo %%equal:~0,%SIZE%%%
endLocal
echo.
echo ====================================================================================================
echo. & echo  [*] Choose a Option
      echo    ^|
      echo    ^|-- [1] EN
      echo    ^|
      echo    ^|
      echo    ^|-- [2] CN
      echo    ^|
      echo    ^|
      echo    ^|-- [3] JP
      echo.
echo. & echo  [4] Updater
echo. & echo  [5] Settings
echo ====================================================================================================
set choice=0
set /p choice= Please input the option and press ENTER:
echo. & echo.
if "%choice%"=="1" goto en
if "%choice%"=="2" goto cn
if "%choice%"=="3" goto jp
if "%choice%"=="4" goto Updater_menu
if "%choice%"=="5" goto setting
echo. & echo Please input a valid option.
pause > NUL
goto MENU

rem ================= OPTION 1 =================

:en
call :CheckBsBeta
call :AdbConnect
rem call :uiautomator2init
echo ====================================================================================================
echo Python Found in %pyBin% Proceeding..
echo Opening alas_en.pyw in %root%
%pyBin% alas_en.pyw
echo Press any key to back main menu
pause > NUL
goto :MENU

rem ================= OPTION 2 =================

:cn
call :CheckBsBeta
call :AdbConnect
rem call :uiautomator2init
echo ====================================================================================================
echo Python Found in %pyBin% Proceeding..
echo Opening alas_en.pyw in %root%
%pyBin% alas_cn.pyw
echo Press any key to back main menu
pause > NUL
goto :MENU

rem ================= OPTION 3 =================
:jp
call :CheckBsBeta
call :AdbConnect
rem call :uiautomator2init
echo ====================================================================================================
echo Python Found in %pyBin% Proceeding..
echo Opening alas_en.pyw in %root%
%pyBin% alas_jp.pyw
echo Press any key to back main menu
pause > NUL
goto :MENU

rem ================= OPTION 4 =================
:Updater_menu
cls
setLocal EnableDelayedExpansion
set "STR=Alas Updater Tool^!"
set "SIZE=100"
set "LEN=0"
:strLen_Loop
   if not "!!STR:~%LEN%!!"=="" set /A "LEN+=1" & goto :strLen_Loop
set "equal====================================================================================================="
set "spaces====================================================================================================="
call echo %%equal:~0,%SIZE%%%
set /a "pref_len=%SIZE%-%LEN%-2"
set /a "pref_len/=2"
set /a "suf_len=%SIZE%-%LEN%-2-%pref_len%"
call echo =%%spaces:~0,%pref_len%%%%%STR%%%%spaces:~0,%suf_len%%%=
call echo %%equal:~0,%SIZE%%%
endLocal
echo.
echo ====================================================================================================
echo Chinese users may need setup proxy or region first, check if settings below are correct.
echo Region: %Region%
echo ====================================================================================================
echo. & echo  [*] Choose a Option
      echo    ^|
      echo    ^|-- [1] Update Alas
      echo    ^|
      echo    ^|
      echo    ^|-- [2] Update dependencies (Toolkit)
      echo    ^|
      echo    ^|
      echo.
echo. & echo  [3] Settings
echo. & echo  [0] Return to the Main Menu
echo ====================================================================================================
set choice=-1
set /p choice= Please input the option and press ENTER:
echo. & echo.
if "%choice%"=="1" goto Run_UpdateAlas
if "%choice%"=="2" goto update_toolkit
if "%choice%"=="3" goto Setting
if "%choice%"=="0" goto MENU
echo. & echo Please input a valid option.
pause > NUL
goto Updater_menu

:Run_UpdateAlas
set source="origin"
if "%Region%"=="cn" set "source=gitee"
echo. & echo.
echo ====================================================================================================
echo Branch in use: %Branch%
echo KeepLocalChanges is: %KeepLocalChanges%
echo ====================================================================================================
set opt6_opt4_choice=0
echo. & echo Change default Branch (master/dev), please enter T;
echo To proceed update using Branch: %Branch%, please enter Y;
echo Back to Updater menu, please enter N;
set /p opt6_opt4_choice= Press ENTER to cancel: 
echo.
if /i "%opt6_opt4_choice%"=="T" (
   call command\Config.bat Branch
) else if /i "%opt6_opt4_choice%"=="Y" (
   goto proceed_alas
) else if /i "%opt6_opt4_choice%"=="N" (
   goto ReturnToMenu
) else (
   echo Invalid input. Cancelled.
   goto ReturnToMenu
)
:proceed_alas
if "%KeepLocalChanges%"=="disable" (
   echo GIT Found in %gitBin% Proceeding
   echo Updating from %source% repository..
   pause
   %gitBin% fetch %source% %Branch%
   %gitBin% reset --hard %source%/%Branch%
   %gitBin% pull --ff-only %source% %Branch%
   echo DONE!
   echo Press any key to proceed
   pause > NUL
   goto Updater_menu
) else (
   echo GIT Found in %gitBin% Proceeding
   echo Updating from %source% repository..
   %gitBin% stash
   %gitBin% pull %source% %Branch%
   %gitBin% stash pop
   echo DONE!
   echo Press any key to proceed
   pause > NUL
   goto Updater_menu
)
echo. & echo Please re-run this batch to make the settings take effect.
echo Please re-run the "alas.bat" to make the settings take effect.
goto PleaseRerun

:update_toolkit
echo is not done yet
pause > NUL
goto ReturnToSetting

rem ================= OPTION 5 =================

:Setting
cls
setLocal EnableDelayedExpansion
set "STR2=Advanced Settings^!"
set "SIZE=100"
set "LEN=0"
:strLen_Loop
   if not "!!STR2:~%LEN%!!"=="" set /A "LEN+=1" & goto :strLen_Loop
set "equal====================================================================================================="
set "spaces====================================================================================================="
call echo %%equal:~0,%SIZE%%%
set /a "pref_len=%SIZE%-%LEN%-2"
set /a "pref_len/=2"
set /a "suf_len=%SIZE%-%LEN%-2-%pref_len%"
call echo =%%spaces:~0,%pref_len%%%%%STR2%%%%spaces:~0,%suf_len%%%=
call echo %%equal:~0,%SIZE%%%
endLocal
echo.
echo. & echo  [0] Return to the Main Menu
echo. & echo  [1] Select Download Region
echo. & echo  [2] Set Global Proxy
echo. & echo  [3] Set SERIAL (For ADB connect)
echo. & echo  [4] (Disable/Enable) Network connection test while updating
echo. & echo  [5] (Disable/Enable) Realtime Connection Mode (Only Bluestacks Beta)
echo. & echo  [6] (Disable/Enable) Keep local changes
echo. & echo  [7] Change default Branch to update (master/dev)
echo. & echo  [8] Reset Settings
echo. & echo.
echo ====================================================================================================
set opt2_choice=-1
set /p opt2_choice= Please input the index number of option and press ENTER:
echo. & echo.
if "%opt2_choice%"=="0" goto MENU
if "%opt2_choice%"=="1" goto Region_setting
if "%opt2_choice%"=="2" goto Proxy_setting
if "%opt2_choice%"=="3" goto Serial_setting
if "%opt2_choice%"=="4" goto NetworkTest_setting
if "%opt2_choice%"=="5" goto Realtime_mode
if "%opt2_choice%"=="6" goto Keep_local_changes
if "%opt2_choice%"=="7" goto Branch_setting
if "%opt2_choice%"=="8" goto Reset_setting
echo Please input a valid option.
goto ReturnToSetting

:Branch_setting
call command\Config.bat Branch
goto ReturnToSetting

:Reset_setting
echo. & echo After updating this batch, if the new settings cannot be toggled, you need to delete "config\deploy.ini". & echo But this will reset all the above settings to default.
set opt3_opt10_choice=0
echo. & echo To delete the settings, please enter Y;
set /p opt3_opt10_choice= Press ENTER to cancel:
echo.
if /i "%opt3_opt10_choice%"=="Y" (
   del /Q config\deploy.ini >NUL 2>NUL
   echo The "config\deploy.ini" has been deleted, please try changing the settings again.
) else ( echo Invalid input. Cancelled. )
goto PleaseRerun

:Serial_setting
echo. & echo.
echo If AdbConnect is enable, the Serial of current CMD window will be:
echo     Current Serial = %Serial%
set opt6_op5_choice=0
echo. & echo Would you like to change the current SERIAL?, please enter Y to proceed;
set /p opt6_op5_choice= Press ENTER to cancel: 
echo.
setlocal EnableDelayedExpansion
if /i "%opt6_op5_choice%"=="Y" (
   set /p opt6_op5_choice= Please input - SERIAL ^(DEFAULT 127.0.0.1:5555 ^): 
   if "!opt6_op5_choice!"=="" ( set "opt6_op5_choice=127.0.0.1:5555" )
   call command\Config.bat Serial !opt6_op5_choice!
   echo.
   echo The serial was set successfully.
) else (
   echo Invalid input. Cancelled.
   goto ReturnToSetting
)
endlocal
echo. & echo Please re-run this batch to make the settings take effect.
echo Please re-run the "alas.bat" to make the settings take effect.
goto PleaseRerun

:Region_setting
echo The current Download Region is: %Region%
echo Chinese users, it is recommended to switch to Gitee, Option [2]
echo [1] Origin (Github) ; [2] CN mirror (Gitee)
set opt3_choice=-1
set /p opt3_choice= Please input the option and press ENTER:
echo. & echo.
if "%opt3_choice%"=="1" ( call command\Config.bat Region origin && goto PleaseRerun )
if "%opt3_choice%"=="2" ( call command\Config.bat Region cn && goto PleaseRerun )
goto ReturnToSetting

:Realtime_mode
call command\Config.bat RealtimeMode
goto ReturnToSetting

:Keep_local_changes
call command\Config.bat KeepLocalChanges
goto ReturnToSetting

:Proxy_setting
call command\Get.bat Proxy
if "%state_globalProxy%"=="enable" (
   echo Global Proxy: enabled
) else ( echo Global Proxy: disabled ^(DEFAULT^) )
echo. & echo.
echo If Global Proxy is enabled, the Proxy Server of current CMD window will be:
echo     HTTP_PROXY  = %__proxyHost%:%__httpPort%
echo     HTTPS_PROXY = %__proxyHost%:%__httpsPort%
set opt6_opt3_choice=0
echo. & echo To (disable/enable) the Global Proxy, please enter T;
echo To reset to the default Proxy Server, please enter Y;
echo To customize the Proxy Host or Port, please enter N;
set /p opt6_opt3_choice= Press ENTER to cancel: 
echo.
setlocal EnableDelayedExpansion
if /i "%opt6_opt3_choice%"=="T" (
   call command\Config.bat Proxy
) else if /i "%opt6_opt3_choice%"=="Y" (
   call command\Config.bat ProxyHost http://127.0.0.1
   call command\Config.bat HttpPort 1080
   call command\Config.bat HttpsPort 1080
   echo The Proxy Server has been reset to the default.
   call command\Config.bat Proxy enable
) else if /i "%opt6_opt3_choice%"=="N" (
   set /p opt6_opt3_proxyHost= Please input - Proxy Host ^(DEFAULT http://127.0.0.1 ^): 
   set /p opt6_opt3_httpPort= Please input - Http Port ^(DEFAULT 1080 ^): 
   set /p opt6_opt3_httpsPort= Please input - Https Port ^(DEFAULT 1080 ^): 
   if "!opt6_opt3_proxyHost!"=="" ( set "opt6_opt3_proxyHost=http://127.0.0.1" )
   if "!opt6_opt3_httpPort!"=="" ( set "opt6_opt3_httpPort=1080" )
   if "!opt6_opt3_httpsPort!"=="" ( set "opt6_opt3_httpsPort=1080" )
   call command\Config.bat ProxyHost !opt6_opt3_proxyHost!
   call command\Config.bat HttpPort !opt6_opt3_httpPort!
   call command\Config.bat HttpsPort !opt6_opt3_httpsPort!
   echo.
   call command\Config.bat Proxy enable
   echo The custom Proxy Server has been set successfully.
   echo Please re-perform this step here to confirm the modification.
) else (
   echo Invalid input. Cancelled.
   goto ReturnToSetting
)
endlocal
echo. & echo Please re-run this batch to make the settings take effect.
echo Please re-run the "alas.bat" to make the settings take effect.
goto PleaseRerun

:Wget_setting
echo The current options of 'wget' are:
set "WgetOptions="
cd toolkit && call command\Get.bat WgetOptions
echo. & echo "%WgetOptions%"
if NOT exist wget.ini ( call command\WgetOptionsGenerator.bat )
cd ..
echo. & echo Edit the "toolkit\wget.ini" manually to change the default options.
echo Please re-perform this step here to confirm the modification.
set opt6_opt6_choice=0
echo. & echo To reset the default "wget.ini", please enter Y;
set /p opt6_opt6_choice= Press ENTER to cancel: 
echo.
if /i "%opt6_opt6_choice%"=="Y" (
   cd toolkit && call command\WgetOptionsGenerator.bat
   cd .. && echo The "wget.ini" has been reset.
) else ( echo Invalid input. Cancelled. )
goto ReturnToSetting

:NetworkTest_setting
call command\Config.bat NetTest
goto ReturnToSetting

:Upgrade_setting
call command\Config.bat UpgradeOnlyViaGitHub
goto ReturnToSetting

rem ================= FUNCTIONS =================

:ReturnToSetting
echo. & echo Press any key to continue...
pause > NUL
goto Setting

:ReturnToMenu
echo. & echo Press any key to continue...
pause > NUL
goto MENU

:PleaseRerun
echo. & echo Press any key to exit...
pause > NUL
exit

:ExitIfGit
:: Check whether already exist .git folder
if exist .git\ (
   echo. & echo The Initial Deployment has been done. Please delete the ".git" folder before performing this action.
   call :PleaseRerun
)
goto :eof

:CheckBsBeta
if "%RealtimeMode%"=="disable" goto :eof
rem if "%FirstRun%"=="enable" goto :eof
echo Connecting with realtime mode...
for /f "tokens=3" %%a in ('reg query HKEY_LOCAL_MACHINE\SOFTWARE\BlueStacks_bgp64_hyperv\Guests\Android\Config /v BstAdbPort') do (set /a port = %%a)
set SerialRealtime=127.0.0.1:%port%
echo ====================================================================================================
echo connecting at %SerialRealtime%
%adbBin% connect %SerialRealtime%
echo ====================================================================================================
if "%FirstRun%"=="yes" (
   call command\ConfigTemplate.bat SerialTemplate %SerialRealtime%
) else (
   call command\ConfigAlas.bat SerialAlas %SerialRealtime%
)
echo ====================================================================================================
echo Old Serial:      %SerialAlas%
echo New Serial:      %SerialRealtime% 
echo ====================================================================================================
echo Press any to continue...
pause > NUL
:: -----------------------------------------------------------------------------
goto :eof

:AdbConnect
if "%RealtimeMode%"=="enable" goto :eof
if "%FirstRun%"=="yes" ( %adbBin% connect %serial_input% && goto :eof )
%adbBin% connect %Serial%
goto :eof

:KillAdb
if "%RealtimeMode%"=="enable" goto :eof
%adbBin% kill-server > nul 2>&1
goto :eof

:uiautomator2init
echo ====================================================================================================
echo initializing uiautomator2
%pyBin% -m uiautomator2 init
echo ====================================================================================================
echo Press any to continue...
pause > NUL
goto :eof

:UpdateChecker_Alas
if "%IsUsingGit%"=="no" goto :eof
if "%Region%"=="cn" goto UpdateChecker_AlasGitee
for /f %%i in ('%gitBin%  rev-parse --abbrev-ref HEAD') do set cfg_branch=%%i
"%curlBin%" -s https://api.github.com/repos/lmeszinc/AzurLaneAutoScript/commits/%cfg_branch%?access_token=%GithubToken% > "%root%\toolkit\api_git.json"
for /f "skip=1 tokens=2 delims=:," %%I IN (%root%\toolkit\api_git.json) DO IF NOT DEFINED sha SET sha=%%I 
set sha=%sha:"=%
set sha=%sha: =%
for /f "skip=14 tokens=3 delims=:" %%I IN (%root%\toolkit\api_git.json) DO IF NOT DEFINED message SET message=%%I 
set message=%message:"=%
set message=%message:,=%
set message=%message:\n=%
for /f %%i in ('%gitBin%  rev-parse --abbrev-ref HEAD') do set BRANCH=%%i
for /f "delims=" %%i IN ('%gitBin% log -1 "--pretty=%%H"') DO set LAST_LOCAL_GIT=%%i
for /f "tokens=1,2" %%A in ('%gitBin% log -1 "--format=%%h %%ct" -- .') do (
set GIT_SHA1=%%A
call :gmTime GIT_CTIME %%B
)

:UpdateChecker_AlasGitee
if "%Region%"=="origin" goto time_parsed
for /f %%i in ('%gitBin%  rev-parse --abbrev-ref HEAD') do set cfg_branch=%%i
"%curlBin%" -s https://gitee.com/api/v5/repos/lmeszinc/AzurLaneAutoScript/commits/%cfg_branch% > "%root%\toolkit\api_git.json"
for /f "tokens=5 delims=:," %%I IN (%root%\toolkit\api_git.json) DO IF NOT DEFINED sha SET sha=%%I 
set sha=%sha:"=%
set sha=%sha: =%
for /f "tokens=25 delims=:" %%I IN (%root%\toolkit\api_git.json) DO IF NOT DEFINED message SET message=%%I 
set message=%message:"=%
set message=%message:,=%
set message=%message:\ntree=%
for /f %%i in ('%gitBin%  rev-parse --abbrev-ref HEAD') do set BRANCH=%%i
for /f "delims=" %%i IN ('%gitBin% log -1 "--pretty=%%H"') DO set LAST_LOCAL_GIT=%%i
for /f "tokens=1,2" %%A in ('%gitBin% log -1 "--format=%%h %%ct" -- .') do (
set GIT_SHA1=%%A
call :gmTime GIT_CTIME %%B
)
:: -----------------------------------------------------------------------------
:time_parsed
if %LAST_LOCAL_GIT% == %sha% (
   echo ====================================================================================================
   echo Remote Git hash:                   %sha%
   echo Remote Git message:                %message%
   echo ====================================================================================================
   echo Local Git hash:                    %LAST_LOCAL_GIT%
   echo Local commit date:                 %GIT_CTIME%
   echo Current Local Branch:              %BRANCH%
   echo ====================================================================================================
   echo Your ALAS is updated, Press any to continue...
   pause > NUL
   goto :eof
) else (
   echo ====================================================================================================
   echo Remote Git hash:                %sha%
   echo Remote Git message:             %message%
   echo ====================================================================================================
   echo Local Git hash:                 %LAST_LOCAL_GIT%
   echo Local commit date:              %GIT_CTIME%
   echo Current Local Branch:           %BRANCH%
   echo ====================================================================================================
   popup.exe
   choice /t 10 /c yn /d y /m "There is an update for ALAS. Download now?"
   if errorlevel 2 goto :eof
   if errorlevel 1 goto Run_UpdateAlas
)

:gmtime
setlocal
set /a z=%2/86400+719468,d=z%%146097,y=^(d-d/1460+d/36525-d/146096^)/365,d-=365*y+y/4-y/100,m=^(5*d+2^)/153
set /a d-=^(153*m+2^)/5-1,y+=z/146097*400+m/11,m=^(m+2^)%%12+1
set /a h=%2/3600%%24,mi=%2%%3600/60,s=%2%%60
if %m% lss 10 set m=0%m%
if %d% lss 10 set d=0%d%
if %h% lss 10 set h=0%h%
if %mi% lss 10 set mi=0%mi%
if %s% lss 10 set s=0%s%
endlocal & set %1=%y%-%m%-%d% %h%:%mi%:%s%
goto :eof

rem ================= End of File =================