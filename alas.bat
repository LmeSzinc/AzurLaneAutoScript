@SETLOCAL EnableExtensions EnableDelayedExpansion
@echo off
pushd %~dp0
title ALAS run
SET CMD=%SystemRoot%\system32\cmd.exe
:: -----------------------------------------------------------------------------
color 8F
:: -----------------------------------------------------------------------------
goto check_Permissions
:check_Permissions
    echo Administrative permissions required. Detecting permissions...

    net session >nul 2>&1
    if %errorLevel% == 0 (
        echo Success: Administrative permissions confirmed.
        echo Press any to continue...
        pause >nul
        goto continue
    ) else (
        echo Failure: Current permissions inadequate.
    )
    pause >nul
:: -----------------------------------------------------------------------------
:continue
SET ALAS_PATH=%~dp0

SET RENAME="python-3.7.6.amd64"
if exist %RENAME% (
  rename %RENAME% toolkit
)

SET MOVE_P="adb_port.ini"
if exist %MOVE_P% (
  move %MOVE_P% %ALAS_PATH%config
)
SET ADB=%ALAS_PATH%toolkit\Lib\site-packages\adbutils\binaries\adb.exe
SET PYTHON=%ALAS_PATH%toolkit\python.exe
SET GIT=%ALAS_PATH%toolkit\Git\cmd\git.exe
SET LMESZINC=https://github.com/LmeSzinc/AzurLaneAutoScript.git
SET WHOAMIKYO=https://github.com/whoamikyo/AzurLaneAutoScript.git
SET ENV=https://github.com/whoamikyo/alas-env.git
SET GITEE_URL=https://gitee.com/lmeszinc/AzurLaneAutoScript.git
SET ADB_P=%ALAS_PATH%config\adb_port.ini
:: -----------------------------------------------------------------------------

:: -----------------------------------------------------------------------------
call %ADB% kill-server > nul 2>&1
set SCREENSHOT_FOLDER=%~dp0screenshots
if not exist %SCREENSHOT_FOLDER% (
  mkdir %SCREENSHOT_FOLDER%
)
:: -----------------------------------------------------------------------------
::if config\adb_port.ini dont exist, will be created
	if not exist %ADB_P% (
  	cd . > %ADB_P%
		)
:: -----------------------------------------------------------------------------
:prompt
REM if adb_port is empty, prompt HOST:PORT
SET "adb_empty=%~dp0config\adb_port.ini"
for %%A in (%adb_empty%) do if %%~zA==0 (
    echo Enter your HOST:PORT eg: 127.0.0.1:5555 for default bluestacks
	echo If you misstype, you can edit the file in config/adb_port.ini
    set /p adb_input=
	)
:: -----------------------------------------------------------------------------
REM if adb_input = 0 load from adb_port.ini
if [%adb_input%]==[] (
    goto load
	)
REM write adb_input on adb_port.ini
echo %adb_input% >> %ADB_P%
:: -----------------------------------------------------------------------------
:: Will search for 127.0.0.1:62001 and replace for %ADB_PORT%
:FINDSTR
setlocal enableextensions disabledelayedexpansion
SET "template=%~dp0config\template.ini"
SET "search=127.0.0.1:62001"
SET "replace=%adb_input%"
SET "string=%template%"
for /f "delims=" %%i in ('type "%string%" ^& break ^> "%string%" ') do (
    SET "line=%%i"
    setlocal enabledelayedexpansion
    >>"%string%" echo(!line:%search%=%replace%!
    endlocal
)
:: -----------------------------------------------------------------------------
:load
REM Load adb_port.ini
REM 
SET /p ADB_PORT=<%ADB_P%
echo connecting at %ADB_PORT%
call %ADB% connect %ADB_PORT%
:: -----------------------------------------------------------------------------
echo initializing uiautomator2
call %PYTHON% -m uiautomator2 init
:: timout
goto alas
:: -----------------------------------------------------------------------------
:alas
color 8F
	cls
	echo.
	echo  :: Alas run
	echo. 
	echo  Choose your option
    echo.
    echo	1. EN
	echo	2. CN
	echo	3. JP
	echo	4. UPDATER
	echo. 
	echo  :: Type a 'number' and press ENTER
	echo  :: Type 'exit' to quit
	echo.
	
	set /P menu=
		if %menu%==1 GOTO en
		if %menu%==2 GOTO cn
		if %menu%==3 GOTO jp
		if %menu%==4 GOTO choose_update_mode
		if %menu%==exit GOTO EOF
		
		else (
		cls
	echo.
	echo  :: Incorrect Input Entered
	echo.
	echo     Please type a 'number' or 'exit'
	echo     Press any key to retry to the menu...
	echo.
		pause > NUL
		goto alas
		)
:: -----------------------------------------------------------------------------
:en
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found in %PYTHON% Proceeding..
	echo Opening alas_en.pyw in %ALAS_PATH%
	call %PYTHON% alas_en.pyw
	goto alas
	) else (
		echo :: it was not possible to open alas_en.pyw, make sure you have a folder toolkit
		echo :: inside AzurLaneAutoScript folder.
		echo Alas PATH: %ALAS_PATH%
		echo Python Path: %PYTHON%
		echo.
        pause > NUL
        goto alas
	)
:: -----------------------------------------------------------------------------
:cn
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found in %PYTHON% Proceeding..
	echo Opening alas_en.pyw in %ALAS_PATH%
	call %PYTHON% alas_cn.pyw
	goto alas
	) else (
		echo :: it was not possible to open alas_cn.pyw, make sure you have a folder toolkit
		echo :: inside AzurLaneAutoScript folder.
		echo Alas PATH: %ALAS_PATH%
		echo Python Path: %PYTHON%
		echo.
        pause > NUL
        goto alas
	)
:: -----------------------------------------------------------------------------
:jp
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found in %PYTHON% Proceeding..
	echo Opening alas_en.pyw in %ALAS_PATH%
	call %PYTHON% alas_jp.pyw
	goto alas
	) else (
		echo :: it was not possible to open alas_jp.pyw, make sure you have a folder toolkit
		echo :: inside AzurLaneAutoScript folder.
		echo Alas PATH: %ALAS_PATH%
		echo Python Path: %PYTHON%
		echo.
        pause > NUL
        goto alas
	)
:: -----------------------------------------------------------------------------
:updater_menu
	cls
	echo.
	echo	:: This update only will work if you downloaded ALAS on
	echo	:: Release tab and installed with Easy_Install-v2.bat
	echo.
	echo	::Overwrite local changes::
	echo.
	echo.
	echo	1) https://github.com/LmeSzinc/AzurLaneAutoScript (Main Repo, When in doubt, use it)
	echo	2) https://github.com/whoamikyo/AzurLaneAutoScript (Mirrored Fork)
	echo	3) https://github.com/whoamikyo/AzurLaneAutoScript (nightly build, dont use)
	echo	4) https://gitee.com/lmeszinc/AzurLaneAutoScript.git (Recommended for CN users)
	echo	5) Back to main menu
	echo.
	echo	:: Type a 'number' and press ENTER
	echo	:: Type 'exit' to quit
	echo.

	set /P choice=
		if %choice%==1 GOTO LmeSzinc
		if %choice%==2 GOTO whoamikyo
		if %choice%==3 GOTO nightly
		if %choice%==4 GOTO gitee
		if %choice%==5 GOTO alas
		if %choice%==exit GOTO EOF
		
		else (
		cls
	echo.
	echo  :: Incorrect Input Entered
	echo.
	echo     Please type a 'number' or 'exit'
	echo     Press any key to return to the menu...
	echo.
		pause > NUL
		goto alas
		)
:: -----------------------------------------------------------------------------
:update_menu_local
	cls
	echo.
	echo	:: This update only will work if you downloaded ALAS on
	echo	:: Release tab and installed with Easy_Install-v2.bat
	echo.
	echo	::Keep local changes::
	echo.
	echo.
	echo	1) https://github.com/LmeSzinc/AzurLaneAutoScript (Main Repo, When in doubt, use it)
	echo	2) https://github.com/whoamikyo/AzurLaneAutoScript (Mirrored Fork)
	echo	3) https://github.com/whoamikyo/AzurLaneAutoScript (nightly build, dont use)
	echo	4) https://gitee.com/lmeszinc/AzurLaneAutoScript.git (Recommended for CN users)
	echo	5) Back to main menu
	echo.
	echo	:: Type a 'number' and press ENTER
	echo	:: Type 'exit' to quit
	echo.

	set /P choice=
		if %choice%==1 GOTO LmeSzinc_local
		if %choice%==2 GOTO whoamikyo_local
		if %choice%==3 GOTO nightly_local
		if %choice%==4 GOTO gitee_local
		if %choice%==5 GOTO alas
		if %choice%==exit GOTO EOF
		
		else (
		cls
	echo.
	echo  :: Incorrect Input Entered
	echo.
	echo     Please type a 'number' or 'exit'
	echo     Press any key to return to the menu...
	echo.
		pause > NUL
		goto alas
		)
:: -----------------------------------------------------------------------------
:LmeSzinc
	call %GIT% --version >nul
	if %errorlevel% == 0 (
	echo GIT Found in %GIT% Proceeding 
	echo Updating from LmeSzinc repository..
	call %GIT% fetch origin master
	call %GIT% reset --hard origin/master
	call %GIT% pull --ff-only origin master
	echo DONE!
	echo Press any key to proceed
	pause > NUL
	goto updater_menu
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
		echo.
        pause > NUL
        goto alas
	)
:: -----------------------------------------------------------------------------
:whoamikyo
	call %GIT% --version >nul
	if %errorlevel% == 0 (
	echo GIT Found in %GIT% Proceeding 
	echo Updating from whoamikyo repository..
	call %GIT% fetch whoamikyo master
	call %GIT% reset --hard whoamikyo/master
	call %GIT% pull --ff-only whoamikyo master
	echo DONE!
	echo Press any key to proceed
	pause > NUL
	goto updater_menu
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
        pause > NUL
        goto alas
	)
:: -----------------------------------------------------------------------------
:nightly
	call %GIT% --version >nul
	if %errorlevel% == 0 (
	echo GIT Found in %GIT% Proceeding 
	echo Updating from whoamikyo nightly repository..
	call %GIT% fetch whoamikyo nightly
	call %GIT% reset --hard whoamikyo/nightly
	call %GIT% pull --ff-only whoamikyo nightly
	echo Press any key to proceed
	pause > NUL
	goto alas
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
		echo.
        pause > NUL
        goto alas
	)
:: -----------------------------------------------------------------------------
:gitee
	call %GIT% --version >nul
	if %errorlevel% == 0 (
	echo GIT Found in %GIT% Proceeding 
	echo Updating from LmeSzinc repository..
	call %GIT% fetch lmeszincgitee master
	call %GIT% reset --hard lmeszincgitee/master
	call %GIT% pull --ff-only lmeszincgitee master
	echo DONE!
	echo Press any key to proceed
	pause > NUL
	goto updater_menu
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
        pause > NUL
        goto alas
	)
:: -----------------------------------------------------------------------------
rem :check_connection
rem cls
rem 	echo.
rem 	echo  :: Checking For Internet Connection to Github...
rem 	echo.
rem 	timeout /t 2 /nobreak > NUL

rem 	ping -n 1 google.com -w 20000 >nul

rem 	if %errorlevel% == 0 (
rem 	echo You have a good connection with Github! Proceeding...
rem 	echo press any to proceed
rem 	pause > NUL
rem 	goto updater_menu
rem 	) else (
rem 		echo  :: You don't have a good connection out of China
rem 		echo  :: It might be better to update using Gitee
rem 		echo  :: Redirecting...
rem 		echo.
rem         echo     Press any key to continue...
rem         pause > NUL
rem         goto start_gitee
rem 	)
:: -----------------------------------------------------------------------------
:toolkit
	call %GIT% --version >nul
	if %errorlevel% == 0 (
	echo GIT Found in %GIT% Proceeding 
	echo Updating toolkit..
	call cd toolkit
	echo ## initializing toolkit..
	call %GIT% init
	call %GIT% config --global core.autocrlf false
	echo ## Adding files
	call %GIT% add -A
	echo ## adding origin..
	call %GIT% remote add origin %ALAS_ENV%
	echo Fething...
	call %GIT% fetch origin master
	call %GIT% reset --hard origin/master
	echo Pulling...
	call %GIT% pull --ff-only origin master
	call cd ..
	echo DONE!
	echo Press any key to proceed
	pause > NUL
	goto updater_menu
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
        pause > NUL
        goto updater_menu
	)
:: -----------------------------------------------------------------------------
rem Keep local changes
:: -----------------------------------------------------------------------------
:choose_update_mode
color 7C
	cls
	echo.
	echo.
	echo	::Choose update method::
	echo.
	echo	1) Overwrite local changes (Will undo any local changes)
	echo	2) Keep local changes (Useful if you have customized a map)
	echo	3) Back to main menu
	echo.
	echo	:: Type a 'number' and press ENTER
	echo	:: Type 'exit' to quit
	echo.

	set /P choice=
		if %choice%==1 GOTO updater_menu
		if %choice%==2 GOTO update_menu_local
		if %choice%==3 GOTO alas
		if %choice%==exit GOTO EOF
		
		else (
		cls
	echo.
	echo  :: Incorrect Input Entered
	echo.
	echo     Please type a 'number' or 'exit'
	echo     Press any key to return to the menu...
	echo.
		pause > NUL
		goto alas
		)
:: -----------------------------------------------------------------------------
:LmeSzinc_local
	call %GIT% --version >nul
	if %errorlevel% == 0 (
	echo GIT Found in %GIT% Proceeding 
	echo Updating from LmeSzinc repository..
	call %GIT% stash
	call %GIT% pull origin master
	call %GIT% stash pop
	echo DONE!
	echo Press any key to proceed
	pause > NUL
	goto update_menu_local
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
		echo.
        pause > NUL
        goto alas
	)
:: -----------------------------------------------------------------------------
:whoamikyo_local
	call %GIT% --version >nul
	if %errorlevel% == 0 (
	echo GIT Found in %GIT% Proceeding 
	echo Updating from whoamikyo repository..
	call %GIT% stash
	call %GIT% pull whoamikyo master
	call %GIT% stash pop
	echo DONE!
	echo Press any key to proceed
	pause > NUL
	goto update_menu_local
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
        pause > NUL
        goto alas
	)
:: -----------------------------------------------------------------------------
:nightly_local
	call %GIT% --version >nul
	if %errorlevel% == 0 (
	echo GIT Found in %GIT% Proceeding 
	echo Updating from whoamikyo nightly repository..
	call %GIT% stash
	call %GIT% pull whoamikyo nightly
	call %GIT% stash pop
	echo Press any key to proceed
	pause > NUL
	goto update_menu_local
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
		echo.
        pause > NUL
        goto alas
	)
:: -----------------------------------------------------------------------------
:gitee_local
	call %GIT% --version >nul
	if %errorlevel% == 0 (
	echo GIT Found in %GIT% Proceeding 
	echo Updating from LmeSzinc repository..
	call %GIT% stash
	call %GIT% pull lmeszincgitee master
	call %GIT% stash pop
	echo DONE!
	echo Press any key to proceed
	pause > NUL
	goto update_menu_local
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
        pause > NUL
        goto alas
	)
:: -----------------------------------------------------------------------------
::Add paths
rem call :AddPath %ALAS_PATH%
rem call :AddPath %ADB%
rem call :AddPath %PYTHON%
rem call :AddPath %GIT%

rem :UpdateEnv
rem ECHO Making updated PATH go live . . .
rem REG delete HKCU\Environment /F /V TEMPVAR > nul 2>&1
rem setx TEMPVAR 1 > nul 2>&1
rem REG delete HKCU\Environment /F /V TEMPVAR > nul 2>&1
:: -----------------------------------------------------------------------------
rem :AddPath <pathToAdd>
rem ECHO %PATH% | FINDSTR /C:"%~1" > nul
rem IF ERRORLEVEL 1 (
rem 	 REG add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /f /v PATH /t REG_SZ /d "%PATH%;%~1" >> add-paths-detail.log
rem 	IF ERRORLEVEL 0 (
rem 		ECHO Adding   %1 . . . Success! >> add-paths.log
rem 		SET "PATH=%PATH%;%~1"
rem 		rem SET UPDATE=1
rem 	) ELSE (
rem 		ECHO Adding   %1 . . . FAILED. Run this script with administrator privileges. >> add-paths.log
rem 	)	
rem ) ELSE (
rem 	ECHO Skipping %1 - Already in PATH >> add-paths.log
rem 	)
:: -----------------------------------------------------------------------------
rem :AddPath <pathToAdd>
rem ECHO %PATH% | FINDSTR /C:"%~1" > nul
rem IF ERRORLEVEL 1 (
rem 	REG add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /f /v PATH /t REG_SZ /d "%PATH%;%~1"  > nul 2>&1
rem 	IF ERRORLEVEL 0 (
rem 		ECHO Adding   %1 . . . Success!
rem 		SET "PATH=%PATH%;%~1"
rem 		SET UPDATE=1
rem 	) ELSE (
rem 		ECHO Adding   %1 . . . FAILED. Run this script with administrator privileges.
rem 	)	
rem ) ELSE (
rem 	ECHO Skipping %1 - Already in PATH
rem 	)
:: -----------------------------------------------------------------------------
:EOF
exit


