@rem
:: Alas Deploy Tool v4
:: Author: whoamikyo (https://kyo.ninja)
:: Version: 4.0
:: Last updated: 2020-08-22
:: >>> Get updated from: https://github.com/LmeSzinc/AzurLaneAutoScript <<<
@echo off
setlocal EnableDelayedExpansion
set "Version=4.0"
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
call command\Get.bat Proxy
call command\Get.bat InfoOpt6
:: If already deployed, show more info in Option3.
call command\Get.bat InfoOpt3
rem call command\Get.bat InfoOpt4

:: Start of Deployment
title Alas Deploy Tool v4
set "pyBin=%root%\toolkit\python.exe"
set "pyPath=%root%\toolkit\"
set "adbBin=%root%\toolkit\Lib\site-packages\adbutils\binaries\adb.exe"
set "gitBin=%root%\toolkit\Git\mingw64\bin\git.exe"
set "curlBin=%root%\toolkit\Git\mingw64\bin\curl.exe"
set "api_json=%root%\config\api_git.json"
set "AlasConfig=%root%\config\alas.ini"
set "template=%root%\config\template.ini"
set "gitFolder=%root%\.git"

rem ================= Menu =================

:MENU
cd "%root%"
cls
:: Uncomment to debug the configuration that imported from "config\deploy.ini"
rem echo Language: %Language% & echo Region: %Region% & echo SystemType: %SystemType%
rem echo http_proxy: %http_proxy% & echo https_proxy: %https_proxy%
rem echo DeployMode: %DeployMode%
rem echo KeepLocalChanges: %KeepLocalChanges%
rem echo RealtimeMode: %RealtimeMode%
setLocal EnableDelayedExpansion
set "STR=Alas Deploy Tool v4^!"
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
echo. & echo  [1] Choose a Option
      echo    ^|
		echo    ^|--     Type 'start' to begin the installation (New method)
		echo    ^|
		echo    ^|
		echo    ^|--     Type 'legacy' to begin the installation using legacy method (Old method)
		echo    ^|        
echo. & echo  [2] Settings
echo ====================================================
set choice=0
set /p choice= Please input the option and press ENTER:
echo. & echo.
if "%choice%"=="1" goto InitDeploy
if "%choice%"=="start" goto NewDeploy
if "%choice%"=="legacy" goto LegacyDeploy
if "%choice%"=="2" goto Setting
echo. & echo Please input a valid option.
pause > NUL
goto MENU

rem ================= OPTION 1 =================

:InitDeploy
echo. & echo Please choose from start , legacy or 2 .
goto ReturnToMenu

rem ================= start =================

:NewDeploy
call :ExitIfGit
if "%SystemType%"=="32" goto :IsNotX64
echo. & echo SystemType Check Ok, x64 System Detected, Proceeding...
set "DeployMode=New"
set "gitee=https://gitee.com/lmeszinc/AzurLaneAutoScript.git"
set "origin=https://github.com/LmeSzinc/AzurLaneAutoScript.git"
set "origin_option=origin"
if "%Region%"=="cn" set "origin_option=gitee"
echo =========================================================================
echo Cloning repository...
cd %root%
echo =========================================================================
echo == initializing...Region selected: %Region%
%gitBin% init
echo =========================================================================
echo == adding remote gitee: %gitee%
%gitBin% remote add gitee %gitee%
echo =========================================================================
echo == adding remote origin: %origin%
%gitBin% remote add origin %origin%
echo =========================================================================
echo == pulling project from %origin%
%gitBin% pull --ff-only %origin_option% master
echo =========================================================================
echo == The installation was successful
echo Press any key to continue and install python and dependencies
echo =========================================================================
pause > NUL

cd toolkit
rem if exist modules\get-pip.py (
rem    if NOT exist download md download
rem    xcopy /Y modules\get-pip.py download\ > NUL
rem )
rem call command\Download.bat main
rem if NOT exist "%pyBin%\python.exe" call command\DoDeploy.bat Setup python

:edit-python_pth
pushd "%pyPath%"
:: Get the full name of "python3*._pth" -> %py_pth%
rem for /f "delims=" %%i in ('dir /b python*._pth') do ( set "py_pth=%%i" )
rem copy %py_pth% %py_pth%.bak > NUL
rem type NUL > %py_pth%
rem for /f "delims=" %%i in (%py_pth%.bak) do (
rem    set "py_pth_str=%%i"
rem    set py_pth_str=!py_pth_str:#import=import!
rem    echo !py_pth_str!>>%py_pth%
rem )
rem del /Q %py_pth%.bak >NUL 2>NUL

:get-pip
rem xcopy /Y "%root%\toolkit\download\get-pip.py" "%pyBin%" > NUL
rem set "PATH=%pyBin%;%pyBin%\Scripts;%PATH%"
if "%Region%"=="cn" set "pip_option=--index-url=https://pypi.tuna.tsinghua.edu.cn/simple"
rem python get-pip.py %pip_option% --no-warn-script-location
python -m pip install -r %root%\toolkit\requirements.txt %pip_option% --no-warn-script-location
python -m pip install %root%\toolkit\python_Levenshtein-0.12.0-cp37-cp37m-win_amd64.whl --no-warn-script-location
xcopy /Y init.py Lib\site-packages\uiautomator2\ > NUL
echo =========================================================================
echo == requirements.txt already deployed.
echo =========================================================================
rem del /Q get-pip.py >NUL 2>NUL
popd && goto InitLog

rem ================= legacy =================

:LegacyDeploy
echo is not done yet
goto ReturnToMenu
set "DeployMode=Legacy"
set "origin=https://github.com/LmeSzinc/AzurLaneAutoScript.git"
if "%Region%"=="cn" set "origin=https://gitee.com/lmeszinc/AzurLaneAutoScript.git"
set "alas_env=https://github.com/whoamikyo/alas-env.git"
if "%Region%"=="cn" set "alas_env=https://gitee.com/lmeszinc/alas-env.git"
call :ExitIfGit
	%gitBin% --version >nul
	if %errorlevel% == 0 (
	echo Cloning repository
	echo GIT Found! Proceeding..
	echo Cloning repository...
	cd %root%
	echo ## initializing...Region selected: %Region%
	%gitBin% init
	echo ## adding origin: %origin%..
	%gitBin% remote add origin %origin%
	echo ## pulling project from %origin%
	%gitBin% pull --ff-only origin master
	echo ## setting default branch...
	%gitBin% branch --set-upstream-to=origin/master master
	pause
	echo Updating toolkit..
	call cd toolkit
	echo ## initializing toolkit..
	%gitBin% init
	%gitBin% config --global core.autocrlf false
	echo ## Adding files
	echo ## This process may take a while
	%gitBin% add -A
	echo ## adding origin..
	%gitBin% remote add origin %alas_env%
	echo Fething...
	%gitBin% fetch origin master
	%gitBin% reset --hard origin/master
	echo Pulling...
	%gitBin% pull --ff-only origin master
	echo The installation was successful
	popd && goto ReturnToMenu
	)

rem ================= OPTION 2 =================

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
echo ====================================================
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

:Realtime_mode
call command\Config.bat RealtimeMode
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
echo If Global Proxy is enabled, the Proxy Server of current CMD window will be:
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
echo [1] Origin website (origin) ; [2] CN mirror (cn)
set opt3_choice=-1
set /p opt3_choice= Please input the option and press ENTER:
echo. & echo.
if "%opt3_choice%"=="1" ( call command\Config.bat Region origin && goto PleaseRerun )
if "%opt3_choice%"=="2" ( call command\Config.bat Region cn && goto PleaseRerun )
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

:IsNotX64
echo. & echo It appears that your system is not x64, Please upgrade to an x64 system to proceed.
pause > NUL
exit

:ReturnToSetting
pause > NUL
goto Setting

:ReturnToMenu
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

:Create_Console-Bat
set isInInitDeploy=%~1
call command\GenerateConsoleBatch.bat %DeployMode%
echo.
echo =========================================================================
if "%isInInitDeploy%"=="1" echo Deployment done.
echo The start batch "console.bat" has been created.
echo =========================================================================
goto :eof


:StopIfDisconnected
if exist deploy.ini (
	for /f "tokens=3 delims= " %%i in ('findstr /i "NetTest" deploy.ini') do ( set "state_netTest=%%i" )
)
if "%state_netTest%"=="disable" goto :eof
echo Checking network connection...
wget -q --no-check-certificate %_Remoteres_%/modules/CurrentVersion -O NetTest && set "_isNetConnected=true" || set "_isNetConnected=false"
if exist NetTest del NetTest
if "%_isNetConnected%"=="false" (
	echo Unable to access GitHub, please check your network connection
	pause > NUL
	goto MENU
)
goto :eof

:InitLog
cd ..
call command\Log.bat Init %DeployMode% && call :Create_Console-Bat 1
goto ReturnToMenu

rem ================= End of File =================