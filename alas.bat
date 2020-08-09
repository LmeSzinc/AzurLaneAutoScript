@echo off
pushd %~dp0
title ALAS run
set CMD=%SystemRoot%\system32\cmd.exe
:: -----------------------------------------------------------------------------
call :check_Permissions
:check_Permissions
    echo Administrative permissions required. Detecting permissions...
    net session >nul 2>&1
    if %errorLevel% == 0 (
        echo Success: Administrative permissions confirmed.
        echo Press any to continue...
        pause >nul
        call :continue
    ) else (
        echo Failure: Current permissions inadequate.
    )
    pause >nul
:: -----------------------------------------------------------------------------
:continue
set ALAS_PATH=%~dp0
:: -----------------------------------------------------------------------------
:: Legacy functions
set RENAME="python-3.7.6.amd64"
if exist %RENAME% (
	rename %RENAME% toolkit
)
set MOVE_P="adb_port.ini"
if exist %MOVE_P% (
	move %MOVE_P% %ALAS_PATH%config
)
:: -----------------------------------------------------------------------------
set ADB=%ALAS_PATH%toolkit\Lib\site-packages\adbutils\binaries\adb.exe
set PYTHON=%ALAS_PATH%toolkit\python.exe
set GIT=%ALAS_PATH%toolkit\Git\cmd\git.exe
set LMESZINC=https://github.com/LmeSzinc/AzurLaneAutoScript.git
set WHOAMIKYO=https://github.com/whoamikyo/AzurLaneAutoScript.git
set ALAS_ENV=https://github.com/whoamikyo/alas-env.git
set ALAS_ENV_GITEE=https://gitee.com/lmeszinc/alas-env.git
set GITEE_URL=https://gitee.com/lmeszinc/AzurLaneAutoScript.git
set ADB_P=%ALAS_PATH%config\adb_port.ini
:: -----------------------------------------------------------------------------
set TOOLKIT_GIT=%~dp0toolkit\.git
if not exist %TOOLKIT_GIT% (
	echo You may need to update your dependencies
	echo Press any key to update
	pause > NUL
	call :toolkit_choose
) else (
	call :adb_kill
)
:: -----------------------------------------------------------------------------
:adb_kill
cls
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
set "adb_empty=%~dp0config\adb_port.ini"
for %%A in (%adb_empty%) do if %%~zA==0 (
    echo Enter your HOST:PORT eg: 127.0.0.1:5555 for default bluestacks
	echo If you misstype, you can edit the file in config/adb_port.ini
    set /p adb_input=
	)
:: -----------------------------------------------------------------------------
REM if adb_input = 0 load from adb_port.ini
if [%adb_input%]==[] (
    call :CHECK_BST_BETA
	)
REM write adb_input on adb_port.ini
echo %adb_input% >> %ADB_P%
call :FINDSTR
:: -----------------------------------------------------------------------------
:: Will search for 127.0.0.1:62001 and replace for %ADB_PORT%
:FINDSTR
setlocal enableextensions disabledelayedexpansion
set "template=%~dp0config\template.ini"
set "search=127.0.0.1:62001"
set "replace=%adb_input%"
set "string=%template%"

for /f "delims=" %%i in ('type "%string%" ^& break ^> "%string%" ') do (
    set "line=%%i"
    setlocal enabledelayedexpansion
    >>"%string%" echo(!line:%search%=%replace%!
    endlocal
	)
)
call :CHECK_BST_BETA
:: -----------------------------------------------------------------------------
:CHECK_BST_BETA
reg query HKEY_LOCAL_MACHINE\SOFTWARE\BlueStacks_bgp64_hyperv >nul
if %errorlevel% equ 0 (
	echo Bluestacks Hyper-V BETA detected
	call :realtime_connection
) else (
	call :load
)
:: -----------------------------------------------------------------------------
:realtime_connection
ECHO. Connecting with realtime mode ...
for /f "tokens=3" %%a in ('reg query HKEY_LOCAL_MACHINE\SOFTWARE\BlueStacks_bgp64_hyperv\Guests\Android\Config /v BstAdbPort') do (set /a port = %%a)
set "SERIAL_REALTIME=127.0.0.1:%port%"
echo connecting at %SERIAL_REALTIME%
call %ADB% connect %SERIAL_REALTIME%

set "config=%~dp0config\alas.ini"
set "configtemp=%~dp0config\alastemp.ini"
set /a search=104
set "replace=serial = %SERIAL_REALTIME%"

(for /f "tokens=1*delims=:" %%a IN ('findstr /n "^" "%config%"') do (
    set "Line=%%b"
    IF %%a equ %search% set "Line=%replace%"
    setLOCAL ENABLEDELAYEDEXPANSION
    ECHO(!Line!
    ENDLOCAL
))> %~dp0config\alastemp.ini
del %config%
MOVE %configtemp% %config%
)
call :init
:: -----------------------------------------------------------------------------
:: -----------------------------------------------------------------------------
:load
REM Load adb_port.ini
REM
set /p ADB_PORT=<%ADB_P%
echo connecting at %ADB_PORT%
call %ADB% connect %ADB_PORT%
:: -----------------------------------------------------------------------------
:init
echo initializing uiautomator2
call %PYTHON% -m uiautomator2 init
:: timout
call :alas
:: -----------------------------------------------------------------------------
:alas
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
		if %menu%==1 call :en
		if %menu%==2 call :cn
		if %menu%==3 call :jp
		if %menu%==4 call :choose_update_mode
		if %menu%==exit call :EOF
		else (
		cls
	echo.
	echo  :: Incorrect Input Entered
	echo.
	echo     Please type a 'number' or 'exit'
	echo     Press any key to retry to the menu...
	echo.
		pause > NUL
		call :alas
		)
:: -----------------------------------------------------------------------------
:en
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found in %PYTHON% Proceeding..
	echo Opening alas_en.pyw in %ALAS_PATH%
	call %PYTHON% alas_en.pyw
	call :alas
	) else (
		echo :: it was not possible to open alas_en.pyw, make sure you have a folder toolkit
		echo :: inside AzurLaneAutoScript folder.
		echo Alas PATH: %ALAS_PATH%
		echo Python Path: %PYTHON%
		echo.
        pause > NUL
        call :alas
	)
:: -----------------------------------------------------------------------------
:cn
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found in %PYTHON% Proceeding..
	echo Opening alas_en.pyw in %ALAS_PATH%
	call %PYTHON% alas_cn.pyw
	call :alas
	) else (
		echo :: it was not possible to open alas_cn.pyw, make sure you have a folder toolkit
		echo :: inside AzurLaneAutoScript folder.
		echo Alas PATH: %ALAS_PATH%
		echo Python Path: %PYTHON%
		echo.
        pause > NUL
        call :alas
	)
:: -----------------------------------------------------------------------------
:jp
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found in %PYTHON% Proceeding..
	echo Opening alas_en.pyw in %ALAS_PATH%
	call %PYTHON% alas_jp.pyw
	call :alas
	) else (
		echo :: it was not possible to open alas_jp.pyw, make sure you have a folder toolkit
		echo :: inside AzurLaneAutoScript folder.
		echo Alas PATH: %ALAS_PATH%
		echo Python Path: %PYTHON%
		echo.
        pause > NUL
        call :alas
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
	echo	5) Toolkit tools updater
	echo	6) Back to main menu
	echo.
	echo	:: Type a 'number' and press ENTER
	echo	:: Type 'exit' to quit
	echo.
	set /P choice=
		if %choice%==1 call :LmeSzinc
		if %choice%==2 call :whoamikyo
		if %choice%==3 call :nightly
		if %choice%==4 call :gitee
		if %choice%==5 call :toolkit_updater
		if %choice%==6 call :alas
		if %choice%==exit call :EOF
		else (
		cls
	echo.
	echo  :: Incorrect Input Entered
	echo.
	echo     Please type a 'number' or 'exit'
	echo     Press any key to return to the menu...
	echo.
		pause > NUL
		call :alas
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
		if %choice%==1 call :LmeSzinc_local
		if %choice%==2 call :whoamikyo_local
		if %choice%==3 call :nightly_local
		if %choice%==4 call :gitee_local
		if %choice%==5 call :alas
		if %choice%==exit call :EOF
		else (
		cls
	echo.
	echo  :: Incorrect Input Entered
	echo.
	echo     Please type a 'number' or 'exit'
	echo     Press any key to return to the menu...
	echo.
		pause > NUL
		call :alas
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
	call :updater_menu
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
		echo.
        pause > NUL
        call :alas
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
	call :updater_menu
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
        pause > NUL
        call :alas
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
	call :alas
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
		echo.
        pause > NUL
        call :alas
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
	call :updater_menu
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
        pause > NUL
        call :alas
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
rem 	call updater_menu
rem 	) else (
rem 		echo  :: You don't have a good connection out of China
rem 		echo  :: It might be better to update using Gitee
rem 		echo  :: Redirecting...
rem 		echo.
rem         echo     Press any key to continue...
rem         pause > NUL
rem         call start_gitee
rem 	)
:: -----------------------------------------------------------------------------
rem Keep local changes
:: -----------------------------------------------------------------------------
:choose_update_mode
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
		if %choice%==1 call :updater_menu
		if %choice%==2 call :update_menu_local
		if %choice%==3 call :alas
		if %choice%==exit call EOF
		else (
		cls
	echo.
	echo  :: Incorrect Input Entered
	echo.
	echo     Please type a 'number' or 'exit'
	echo     Press any key to return to the menu...
	echo.
		pause > NUL
		call :alas
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
	call :update_menu_local
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
		echo.
        pause > NUL
        call :alas
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
	call :update_menu_local
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
        pause > NUL
        call :alas
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
	call :update_menu_local
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
		echo.
        pause > NUL
        call :alas
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
	call :update_menu_local
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
        pause > NUL
        call :alas
	)
:: -----------------------------------------------------------------------------
:toolkit_choose
	cls
	echo.
	echo	:: This will add the toolkit repository for updating
	echo.
	echo	::Toolkit::
	echo.
	echo.
	echo	1) https://github.com/whoamikyo/alas-env.git (Default Github)
	echo	2) https://gitee.com/lmeszinc/alas-env.git (Recommended for CN users)
	echo	3) Back to main menu
	echo.
	echo	:: Type a 'number' and press ENTER
	echo	:: Type 'exit' to quit
	echo.
	set /P choice=
		if %choice%==1 call :toolkit_github
		if %choice%==2 call :toolkit_gitee
		if %choice%==3 call :alas
		if %choice%==exit call :EOF
		else (
		cls
	echo.
	echo  :: Incorrect Input Entered
	echo.
	echo     Please type a 'number' or 'exit'
	echo     Press any key to return to the menu...
	echo.
		pause > NUL
		call :alas
		)
:: -----------------------------------------------------------------------------
:toolkit_github
	call %GIT% --version >nul
	if %errorlevel% == 0 (
	echo GIT Found in %GIT% Proceeding
	echo Updating toolkit..
	call cd toolkit
	echo ## initializing toolkit..
	call %GIT% init
	call %GIT% config --global core.autocrlf false
	echo ## Adding files
	echo ## This process may take a while
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
	call :adb_kill
	) else (
		echo	:: Git not found, maybe there was an installation issue
		echo	:: check if you have this directory %GIT%
        pause > NUL
        call :adb_kill
	)
:: -----------------------------------------------------------------------------
:toolkit_gitee
	call %GIT% --version >nul
	if %errorlevel% == 0 (
	echo GIT Found in %GIT% Proceeding
	echo Updating toolkit..
	call cd toolkit
	echo ## initializing toolkit..
	call %GIT% init
	call %GIT% config --global core.autocrlf false
	echo ## Adding files
	echo ## This process may take a while
	call %GIT% add -A
	echo ## adding origin..
	call %GIT% remote add origin %ALAS_ENV_GITEE%
	echo Fething...
	call %GIT% fetch origin master
	call %GIT% reset --hard origin/master
	echo Pulling...
	call %GIT% pull --ff-only origin master
	call cd ..
	echo DONE!
	echo Press any key to proceed
	pause > NUL
	call :adb_kill
	) else (
		echo	:: Git not found, maybe there was an installation issue
		echo	:: check if you have this directory %GIT%
        pause > NUL
        call :adb_kill
	)
:: -----------------------------------------------------------------------------
:toolkit_updater
	call %GIT% --version >nul
	if %errorlevel% == 0 (
	echo GIT Found in %GIT% Proceeding
	echo Updating toolkit..
	call cd toolkit
	call %GIT% fetch origin master
	call %GIT% reset --hard origin/master
	echo Pulling...
	call %GIT% pull --ff-only origin master
	echo DONE!
	call cd ..
	echo Press any key to proceed
	pause > NUL
	call :updater_menu
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\toolkit\Git\cmd
        pause > NUL
        call :alas
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
rem 	 REG add "HKLM\SYSTEM\CurrentControlset\Control\Session Manager\Environment" /f /v PATH /t REG_SZ /d "%PATH%;%~1" >> add-paths-detail.log
rem 	IF ERRORLEVEL 0 (
rem 		ECHO Adding   %1 . . . Success! >> add-paths.log
rem 		set "PATH=%PATH%;%~1"
rem 		rem set UPDATE=1
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
rem 	REG add "HKLM\SYSTEM\CurrentControlset\Control\Session Manager\Environment" /f /v PATH /t REG_SZ /d "%PATH%;%~1"  > nul 2>&1
rem 	IF ERRORLEVEL 0 (
rem 		ECHO Adding   %1 . . . Success!
rem 		set "PATH=%PATH%;%~1"
rem 		set UPDATE=1
rem 	) ELSE (
rem 		ECHO Adding   %1 . . . FAILED. Run this script with administrator privileges.
rem 	)
rem ) ELSE (
rem 	ECHO Skipping %1 - Already in PATH
rem 	)
:: -----------------------------------------------------------------------------
:EOF
exit
