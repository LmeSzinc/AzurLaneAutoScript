@SETLOCAL EnableExtensions EnableDelayedExpansion
@echo off
pushd "%~dp0"
:: VARIABLES INSTALL

SET CMD=%SystemRoot%\system32\cmd.exe
SET LMESZINC=https://github.com/LmeSzinc/AzurLaneAutoScript.git
SET WHOAMIKYO=https://github.com/whoamikyo/AzurLaneAutoScript.git

rem SET ROOT_UPPER=%~dp0
rem SET ADB_PATH=%AZURLANESCRIPT%\python-3.7.6.amd64\Lib\site-packages\adbutils\binaries

:: -----------------------------------------------------------------------------
:: Make sure we're running with administrator privileges
echo.
echo  :: Checking For Administrator Elevation...
echo.
net session >nul 2>&1
if %errorLevel% == 0 (
        echo Elevation found! Proceeding...
        goto menu
) 	else (
        echo  :: You are NOT running as Administrator
        echo.
        echo     Right-click and select ^'Run as Administrator^' and try again.
        echo     Press any key to exit...
        pause > NUL
        exit
)
REM PowerShell -Command "Start-Sleep -s 3" > nul 2>&1
:: -----------------------------------------------------------------------------

:: Make sure the second path exists. The first path won't be created until the second script is run
rem IF NOT EXIST !ADB_PATH! (ECHO Path not found: %ADB_PATH% && GOTO ExitBatch)
:: -----------------------------------------------------------------------------

:: Add paths
rem CALL :AddPath %ADB_PATH%
rem CALL :AddPath %GIT_PATH%
rem CALL :AddPath %AZURLANESCRIPT%
rem CALL :AddPath %ROOT_UPPER%
pause

:: Branch to UpdateEnv if we need to update
REM IF DEFINED UPDATE (GOTO UpdateEnv)

REM GOTO ExitBatch
:: -----------------------------------------------------------------------------

REM :UpdateEnv
REM ECHO Making updated PATH go live . . .
REM REG delete HKCU\Environment /F /V TEMPVAR > nul 2>&1
REM setx TEMPVAR 1 > nul 2>&1
REM REG delete HKCU\Environment /F /V TEMPVAR > nul 2>&1
REM IF NOT !cmdcmdline! == !CMDLINERUNSTR! (CALL :KillExplorer)
REM GOTO ExitBatch

:: -----------------------------------------------------------------------------
goto menu
:menu
	cls
	echo.
	echo  :: Easy install for ALAS
	echo. 
	echo  This script will install Python 3.7.6 + requirements.txt + ADB + GIT + CHOCOLATEY
	echo.
	echo  :: For fresh install, Run step "1" and "2"
	echo. 
	echo		1.Python 3.7.6 + ADB + GIT + requirements.txt
	echo		2.Clone repository (Download the latest version from LmeSzinc repository)
	echo		3.Programs (ADB + GIT Alternative way with CHOCOLATEY)
	echo		4.Updater ONLY (Do not update if you are doing a fresh install)
	echo.	
	echo		JUST RUN UPDATER INSIDE AzurLaneAutoScript FOLDER
	echo.
	echo		Install in order
	echo. 
	echo  :: Type a 'number' and press ENTER
	echo  :: Type 'exit' to quit
	echo.
	set /P menu=
		if %menu%==1 GOTO python
		if %menu%==2 GOTO clone
		if %menu%==3 GOTO programs
		if %menu%==4 GOTO updater
		if %menu%==exit GOTO EOF
		
		else (
		cls
	echo.
	echo  :: Incorrect Input Entered
	echo.
	echo     Please type a 'number' or 'exit'
	echo     Press any key to return to the menu...
	echo.
		pause > NUL
		goto menu
		)
:: -----------------------------------------------------------------------------
:programs
cls
	echo.
	echo  :: Checking For Internet Connection...
	echo.
	timeout /t 2 /nobreak > NUL

	ping -n 1 archlinux.org -w 20000 >nul

	if %errorlevel% == 0 (
	echo Internet Connection Found! Proceeding..
	) else (
		echo  :: You are NOT connected to the Internet
		echo.
        echo     Please enable your Networking adapter and connect to try again.
        echo     Press any key to retry...
        pause > NUL
        goto packages
	)
		cls
		echo.
		echo  :: Installing Packages ADB + GIT + CHOCOLATEY
		echo  :: If you already have any of these packages installed
		echo  :: you will probably have an error installing that package
		echo  :: you can try to proceed anyway
		echo  :: it might work if there is nothing wrong with the previous installation
		echo  :: if you have problems I suggest uninstalling all packages mentioned in the control panel (windows)
		echo.
		timeout /t 1 /nobreak > NUL
		SET PATH=%PATH%;%PROGRAMDATA%\chocolatey\lib\adb\tools\platform-tools\;%PROGRAMFILES%\Git\cmd;%PROGRAMDATA%\chocolatey\bin
		echo Installing chocolatey on this machine
		@powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ((new-object net.webclient).DownloadString('https://chocolatey.org/install.ps1'))">>chocolatey-%DATE:~-4%-%DATE:~4,2%-%DATE:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log && SET PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin
	)
		echo Installing Essentials programs, It may take
		@powershell -NoProfile -ExecutionPolicy Bypass -Command "choco install -y --force --allow-empty-checksums adb git">>Essentials-%DATE:~-4%-%DATE:~4,2%-%DATE:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
	)
call refreshenv
goto menu
:: -----------------------------------------------------------------------------
:: killing adb server
:killadb
	call %ADB_PATH% --version >nul
	if %errorlevel% == 0 (
	echo ADB Found! Proceeding..
	echo killing adb server..
	call %ADB_PATH% kill-server > nul 2>&1
	goto menu
	) else (
		echo  :: ADB not found, maybe there was an installation issue, try opening another CMD window and type choco install adb
		echo.
        pause > NUL
        goto menu
	)
:: -----------------------------------------------------------------------------
:clone
SET AZURLANESCRIPT=%~dp0AzurLaneAutoScript
SET GIT_PATH=%AZURLANESCRIPT%\python-3.7.6.amd64\Git\cmd
SET GIT=%GIT_PATH%\git.exe
	call %GIT% --version >nul
	if %errorlevel% == 0 (
	echo Cloning repository
	echo GIT Found! Proceeding..
	echo Cloning repository...
	cd %AZURLANESCRIPT%
	echo Deleting folder unused files
	for /D %%D in ("*") do (
    if /I not "%%~nxD"=="python-3.7.6.amd64" rd /S /Q "%%~D"
	)
for %%F in ("*") do (
    del "%%~F"
	)
	echo ## initializing..
	call %GIT% init
	echo ## adding origin..
	call %GIT% remote add origin %LMESZINC%
	echo ## pulling project...
	call %GIT% pull origin master
	echo ## setting default branch...
	call %GIT% branch --set-upstream-to=origin/master master
	call %GIT% remote add whoamikyo %WHOAMIKYO%
	echo The installation was successful
	echo Press any key to proceed
	pause > NUL
	goto menu
	) else (
		echo  :: Git not found, maybe there was an installation issue, try opening another CMD window and type choco install git
		echo.
        pause > NUL
	)
:: -----------------------------------------------------------------------------
:python
cls
echo.
echo  :: Python 3.7.6 + ADB + GIT + requirements.txt
echo.
echo.
SET PYTHON=%~dp0AzurLaneAutoScript/python-3.7.6.amd64/python.exe
SET AZURLANESCRIPT=%~dp0AzurLaneAutoScript
SET FILE_URL=https://gitlab.com/whoamikyo/alas-venv/-/raw/master/python.zip
SET FILE_DEST=%AZURLANESCRIPT%\pythonpackage.zip
if not exist %AZURLANESCRIPT% (
	echo WILL BE CREATED A FOLDER "AzurLaneAutoScript"
	echo DO NOT RENAME THE FOLDER NEVER
  	mkdir %AZURLANESCRIPT%
)
 if not exist "%FILE_DEST%" (
   echo Downloading with powershell: %FILE_URL% to %FILE_DEST%
   powershell.exe -command "$webclient = New-Object System.Net.WebClient; $url = \"%FILE_URL%\"; $file = \"%FILE_DEST%\"; $webclient.DownloadFile($url,$file);"
   echo Expanding with powershell to: %AZURLANESCRIPT%
   powershell -command "$shell_app=new-object -com shell.application; $zip_file = $shell_app.namespace(\"%FILE_DEST%\"); $destination = $shell_app.namespace(\"%AZURLANESCRIPT%\"); $destination.Copyhere($zip_file.items())"
 ) else (
   echo "pythonpackage.zip already downloaded, delete to re-download"
   pause > NUL
 )
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo initializing uiautomator2..
	call %PYTHON% -m uiautomator2 init
	echo The installation was successful
	echo Press any key to proceed
	pause > NUL
	goto menu
	) else (
		echo :: it was not possible to install uiautomator2
		echo :: make sure you have a folder "python-3.7.6.amd64"
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
        goto menu
	)
:: -----------------------------------------------------------------------------
:updater
SET GIT_ALAS=%~dp0python-3.7.6.amd64\Git\cmd\git.exe
SET GLP=%GIT_ALAS%
SET ALAS_PY=alas.py
	if exist %ALAS_PY% (
			goto updater_menu
		) else (
		cd AzurLaneAutoScript
		echo.
		goto updater_menu
	)
:: -----------------------------------------------------------------------------
:updater_menu
	cls
	echo.
	echo  :: This update only will work if you downloaded ALAS with this file using option 2. clone
	echo. 
	echo	::DISCLAIMER::
	echo	IF YOU GET THE FOLLOWING ERROR: 
	echo	"error: Your local changes to the following files would be overwritten by merge:Easy_Install-V2.bat"
	echo	YOU NEED RE-DOWNLOAD ONLY Easy_Install-V2.bat FILE FROM REPOSITORY AND OVERWRITTEN THE OLD FOR NEW FILE	
	echo
	echo					JUST RUN UPDATER INSIDE AzurLaneAutoScript FOLDER
	echo. 
	echo     1. https://github.com/LmeSzinc/AzurLaneAutoScript (Main Repo, When in doubt, use it)
	echo     2. https://github.com/whoamikyo/AzurLaneAutoScript (Mirrored Fork)
	echo     3. https://github.com/whoamikyo/AzurLaneAutoScript (nightly build, dont use)
	echo     4. Back to main menu
	echo. 
	echo  :: Type a 'number' and press ENTER
	echo  :: Type 'exit' to quit
	echo.
	
	set /P choice=
		if %choice%==1 GOTO LmeSzinc
		if %choice%==2 GOTO whoamikyo
		if %choice%==3 GOTO nightly
		if %choice%==4 GOTO menu
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
		goto updater_menu
		)
:: -----------------------------------------------------------------------------
:LmeSzinc
	call %GLP% --version >nul
	if %errorlevel% == 0 (
	echo GIT Found! Proceeding..
	echo Updating from LmeSzinc repository..
	call %GLP% fetch origin master
	call %GLP% reset --hard origin/master
	call %GLP% pull --ff-only origin master
	echo DONE!
	echo Press any key to proceed
	pause > NUL
	goto updater_menu
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\python-3.7.6.amd64\Git\cmd
		echo.
        pause > NUL
	)
:: -----------------------------------------------------------------------------
:whoamikyo
	call %GLP% --version >nul
	if %errorlevel% == 0 (
	echo GIT Found! Proceeding..
	echo Updating from whoamikyo repository..
	call %GLP% fetch whoamikyo master
	call %GLP% reset --hard whoamikyo/master
	call %GLP% pull --ff-only whoamikyo master
	echo DONE!
	echo Press any key to proceed
	pause > NUL
	goto updater_menu
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\python-3.7.6.amd64\Git\cmd
        pause > NUL
        goto updater_menu
	)
:: -----------------------------------------------------------------------------
:nightly
	call %GLP% --version >nul
	if %errorlevel% == 0 (
	echo GIT Found! Proceeding..
	echo Updating from whoamikyo nightly repository..
	call %GLP% fetch whoamikyo nightly
	call %GLP% reset --hard whoamikyo/nightly
	call %GLP% pull --ff-only whoamikyo nightly
	echo Press any key to proceed
	pause > NUL
	goto updater_menu
	) else (
		echo  :: Git not detected, maybe there was an installation issue
		echo check if you have this directory:
		echo AzurLaneAutoScript\python-3.7.6.amd64\Git\cmd
		echo.
        pause > NUL
        goto updater_menu
	)

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
rem EXIT /b

:: -----------------------------------------------------------------------------

rem :KillExplorer

rem ECHO Your desktop is being restarted, please wait. . .   
rem ping -n 5 127.0.0.1 > NUL 2>&1   
rem ECHO Killing process Explorer.exe. . .   
rem taskkill /f /im explorer.exe   
rem ECHO.   
rem ECHO Your desktop is now loading. . .   
rem ping -n 5 127.0.0.1 > NUL 2>&1   
rem ECHO.   
rem ping -n 5 127.0.0.1 > NUL 2>&1   
rem START explorer.exe
rem START explorer.exe %CD%
rem EXIT /b

:: -----------------------------------------------------------------------------
