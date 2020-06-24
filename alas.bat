@SETLOCAL EnableExtensions EnableDelayedExpansion
@echo off
title ALAS run
SET ADB=%~dp0python-3.7.6.amd64\Lib\site-packages\adbutils\binaries\adb.exe
SET PYTHON=%~dp0python-3.7.6.amd64\python.exe

call %ADB% kill-server > nul 2>&1

set SCREENSHOT_FOLDER=%~dp0screenshots
if not exist %SCREENSHOT_FOLDER% (
  mkdir %SCREENSHOT_FOLDER%
)

if not exist adb_port.ini (
  cd . > adb_port.ini
)

REM if adb_port is empty, prompt HOST:PORT
set "adb_empty=*adb_port.ini"
for %%A in (%adb_empty%) do if %%~zA==0 (
    echo enter your HOST:PORT eg: 127.0.0.1:5555 for default bluestacks
	echo WARNING! DONT FORGET TO SETUP AGAIN IN, ALAS ON EMULATOR SETTINGS FUNCTION
    set /p adb_input=
)

REM if adb_input = 0 load from adb_port.ini
if [%adb_input%]==[] (
    goto load
)

REM write adb_input on adb_port.ini
echo %adb_input% >> adb_port.ini

REM Load adb_port.ini
:load
REM 
set /p ADB_PORT=<adb_port.ini

echo connecting at %ADB_PORT%
call %ADB% connect %ADB_PORT%

echo initializing uiautomator2
call %PYTHON% -m uiautomator2 init
:: timout
PowerShell -Command "Start-Sleep -s 4" > nul 2>&1

goto alas

:alas
	cls
	echo.
	echo  :: Alas run
	echo. 
	echo  Choose your server
    echo.
    echo	1. EN
	echo	2. CN
	echo	3. JP
	echo. 
	echo  :: Type a 'number' and press ENTER
	echo  :: Type 'exit' to quit
	echo.
	
	set /P menu=
		if %menu%==1 GOTO en
		if %menu%==2 GOTO cn
		if %menu%==3 GOTO jp
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
		
:en
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening alas_en.pyw...
	call %PYTHON% alas_en.pyw
	) else (
		echo :: it was not possible to open alas_en.pyw, make sure you have a folder python-3.7.6.amd64
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
	)
PowerShell -Command "Start-Sleep -s 10" > nul 2>&1
goto alas
:cn
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening alas_en.pyw...
	call %PYTHON% alas_cn.pyw
	) else (
		echo :: it was not possible to open alas_cn.pyw, make sure you have a folder python-3.7.6.amd64
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
	)
goto alas
:jp
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening alas_en.pyw...
	call %PYTHON% alas_jp.pyw
	) else (
		echo :: it was not possible to open alas_jp.pyw, make sure you have a folder python-3.7.6.amd64
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
	)
goto alas
:EOF
exit


