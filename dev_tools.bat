@echo off
setlocal EnableDelayedExpansion
title Dev_tools

set SCREENSHOT_FOLDER=%~dp0screenshots
if not exist %SCREENSHOT_FOLDER% (
  mkdir %SCREENSHOT_FOLDER%
)

if not exist adb_port.ini (
  cd . > adb_port.ini
)

set "adb_empty=*adb_port.ini"
for %%A in (%adb_empty%) do if %%~zA==0 (
    echo enter your HOST:PORT eg: 127.0.0.1:5555 for default bluestacks
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
adb connect %ADB_PORT%

:dev_menu
	cls
	echo.
	echo  :: Dev_tools
    echo.
    echo	1. emulator_test
	echo	2. button_extract
	echo	3. ADB SCREENSHOT (for ASSETS)
	echo	4. Uiautomator2 SCREENSHOT (for ASSETS)
	echo. 
	echo  :: Type a 'number' and press ENTER
	echo  :: Type 'exit' to quit
	echo.
	
	set /P menu=
		if %menu%==1 GOTO emulator_test
		if %menu%==2 GOTO button_extract
		if %menu%==3 GOTO adbss
		if %menu%==4 GOTO u2ss
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
		goto dev_menu
		)

:emulator_test
%~dp0python-3.7.6.amd64/python.exe -m dev_tools.emulator_test
echo.
PowerShell -Command "Start-Sleep -s 3" > nul 2>&1

goto dev_menu

:button_extract
%~dp0python-3.7.6.amd64/python.exe -m dev_tools.button_extract
echo.
PowerShell -Command "Start-Sleep -s 3" > nul 2>&1

goto dev_menu

:adbss
echo Enter any text/letter instead of the file name, do not enter spaces, enter exit to exit
echo or enter alas to back to main menu
echo.
:set
SET time=%date:~0,4%%date:~5,2%%date:~8,2%%time:~0,2%%time:~3,2%%time:~6,2%
SET name=%time%
SET /P name=
IF /I '%name%'=='exit' goto EOF
IF /I '%name%'=='alas' goto dev_menu
adb -s %ADB_PORT% shell mkdir /sdcard/dcim/Screenshot 2>nul
adb -s %ADB_PORT% shell screencap -p /sdcard/dcim/Screenshot/%name%.png
adb -s %ADB_PORT% pull /sdcard/dcim/Screenshot/%name%.png %SCREENSHOT_FOLDER%\%name%.png
adb -s %ADB_PORT% shell rm /sdcard/dcim/Screenshot/%name%.png
echo.
echo The file %name%.png has been copied to ./screenshots/ directory
echo.
SET time=
PowerShell -Command "Start-Sleep -s 3" > nul 2>&1

goto adbss

:u2ss
%~dp0python-3.7.6.amd64/python.exe -m dev_tools.uiautomator2_screenshot
echo The file *.png has been copied to ./screenshots/ directory
PowerShell -Command "Start-Sleep -s 3" > nul 2>&1
echo.

goto dev_menu


:EOF
exit