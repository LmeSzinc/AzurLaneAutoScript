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
    echo	1.  emulator_test
	echo	2.  button_extract
	echo	3.  grids_debug
	echo	4.  item_stastistics
	echo	5.  relative_crop
	echo	6.  map_extractor
	echo	7.  word_template_extractor
	echo	8. ADB SCREENSHOT (for ASSETS)
	echo	9. Uiautomator2 SCREENSHOT (for ASSETS)
	echo. 
	echo  :: Type a 'number' and press ENTER
	echo  :: Type 'exit' to quit
	echo.
	
	set /P menu=
		if %menu%==1 GOTO emulator_test
		if %menu%==2 GOTO button_extract
		if %menu%==3 GOTO grids_debug
		if %menu%==4 GOTO item_stastistics
		if %menu%==5 GOTO relative_crop
		if %menu%==6 GOTO map_extractor
		if %menu%==7 GOTO word_template_extractor
		if %menu%==8 GOTO adbss
		if %menu%==9 GOTO u2ss
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
	call %~dp0python-3.7.6.amd64/python.exe --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening dev_tools.button_extract...
	%~dp0python-3.7.6.amd64/python.exe -m dev_tools.button_extract
	) else (
		echo :: it was not possible to open dev_tools.button_extract, make sure you have a folder python-3.7.6.amd64
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
	)
PowerShell -Command "Start-Sleep -s 3" > nul 2>&1

goto dev_menu

:grids_debug
	call %~dp0python-3.7.6.amd64/python.exe --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening dev_tools.button_extract...
	%~dp0python-3.7.6.amd64/python.exe -m dev_tools.grids_debug
	) else (
		echo :: it was not possible to open dev_tools.grids_debug, make sure you have a folder python-3.7.6.amd64
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
	)
PowerShell -Command "Start-Sleep -s 10" > nul 2>&1

goto dev_menu

:item_stastistics
	call %~dp0python-3.7.6.amd64/python.exe --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening dev_tools.button_extract...
	%~dp0python-3.7.6.amd64/python.exe -m dev_tools.item_stastistics
	) else (
		echo :: it was not possible to open dev_tools.item_stastistics, make sure you have a folder python-3.7.6.amd64
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
	)
PowerShell -Command "Start-Sleep -s 10" > nul 2>&1

goto dev_menu

:relative_crop
	call %~dp0python-3.7.6.amd64/python.exe --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening dev_tools.button_extract...
	%~dp0python-3.7.6.amd64/python.exe -m dev_tools.relative_crop
	) else (
		echo :: it was not possible to open dev_tools.relative_crop, make sure you have a folder python-3.7.6.amd64
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
	)
PowerShell -Command "Start-Sleep -s 3" > nul 2>&1

goto dev_menu

:map_extractor
	call %~dp0python-3.7.6.amd64/python.exe --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening dev_tools.button_extract...
	%~dp0python-3.7.6.amd64/python.exe -m dev_tools.map_extractor
	) else (
		echo :: it was not possible to open dev_tools.map_extractor, make sure you have a folder python-3.7.6.amd64
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
	)
PowerShell -Command "Start-Sleep -s 3" > nul 2>&1

goto dev_menu

:word_template_extractor
	call %~dp0python-3.7.6.amd64/python.exe --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening dev_tools.button_extract...
	%~dp0python-3.7.6.amd64/python.exe -m dev_tools.word_template_extractor
	) else (
		echo :: it was not possible to open dev_tools.word_template_extractor, make sure you have a folder python-3.7.6.amd64
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
	)
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
call %~dp0python-3.7.6.amd64\Lib\site-packages\adbutils\binaries\adb -s %ADB_PORT% shell mkdir /sdcard/dcim/Screenshot 2>nul
call %~dp0python-3.7.6.amd64\Lib\site-packages\adbutils\binaries\adb -s %ADB_PORT% shell screencap -p /sdcard/dcim/Screenshot/%name%.png
call %~dp0python-3.7.6.amd64\Lib\site-packages\adbutils\binaries\adb -s %ADB_PORT% pull /sdcard/dcim/Screenshot/%name%.png %SCREENSHOT_FOLDER%\%name%.png
call %~dp0python-3.7.6.amd64\Lib\site-packages\adbutils\binaries\adb -s %ADB_PORT% shell rm /sdcard/dcim/Screenshot/%name%.png
echo.
echo The file %name%.png has been copied to ./screenshots/ directory
echo.
SET time=
PowerShell -Command "Start-Sleep -s 3" > nul 2>&1
if NOT ["%errorlevel%"]==["0"] (
    pause
    exit /b %errorlevel%
)
goto adbss

:u2ss
%~dp0python-3.7.6.amd64/python.exe -m dev_tools.uiautomator2_screenshot
echo The file *.png has been copied to ./screenshots/ directory
PowerShell -Command "Start-Sleep -s 3" > nul 2>&1
if NOT ["%errorlevel%"]==["0"] (
    pause
    exit /b %errorlevel%
)
echo.

goto dev_menu


:EOF
exit