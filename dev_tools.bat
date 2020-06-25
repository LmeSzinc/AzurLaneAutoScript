@echo off
setlocal EnableDelayedExpansion
title Dev_tools
pushd "%~dp0"
:: -----------------------------------------------------------------------------
SET ADB_PATH=%~dp0toolkit\Lib\site-packages\adbutils\binaries\adb.exe
SET ADB=%ADB_PATH%
SET PYTHON_PATH=%~dp0toolkit\python.exe
SET PYTHON=%PYTHON_PATH%
:: -----------------------------------------------------------------------------
goto check_Permissions
:check_Permissions
    echo Administrative permissions required. Detecting permissions...

    net session >nul 2>&1
    if %errorLevel% == 0 (
        echo Success: Administrative permissions confirmed.
        pause >nul
        goto continue
    ) else (
        echo Failure: Current permissions inadequate.
    )
    pause >nul
:: -----------------------------------------------------------------------------
:continue
set FILE_PREFIX=screenshot
set SCREENSHOT_FOLDER=%~dp0screenshots
if not exist %SCREENSHOT_FOLDER% (
  mkdir %SCREENSHOT_FOLDER%
)
:: -----------------------------------------------------------------------------
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
CALL %ADB% connect %ADB_PORT%
:: -----------------------------------------------------------------------------
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
	echo	10. ADB SCREENSHOT (Continuous Screenshot)
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
		if %menu%==10 GOTO adbc
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
:: -----------------------------------------------------------------------------
:emulator_test
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening dev_tools.emulator_test...
	call %PYTHON% -m dev_tools.emulator_test
	pause > NUL
	goto dev_menu
	) else (
		echo :: it was not possible to open dev_tools.emulator_test, make sure you have a folder toolkit
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
        goto dev_menu
	)
:: -----------------------------------------------------------------------------
:button_extract
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening dev_tools.button_extract...
	call %PYTHON% -m dev_tools.button_extract
	pause > NUL
	goto dev_menu
	) else (
		echo :: it was not possible to open dev_tools.button_extract, make sure you have a folder toolkit
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
        goto dev_menu
	)
:: -----------------------------------------------------------------------------
:grids_debug
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening dev_tools.button_extract...
	call %PYTHON% -m dev_tools.grids_debug
	pause > NUL
	goto dev_menu
	) else (
		echo :: it was not possible to open dev_tools.grids_debug, make sure you have a folder toolkit
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
        goto dev_menu
	)
:: -----------------------------------------------------------------------------
:item_stastistics
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening dev_tools.button_extract...
	call %PYTHON% -m dev_tools.item_stastistics
	pause > NUL
	goto dev_menu
	) else (
		echo :: it was not possible to open dev_tools.item_stastistics, make sure you have a folder toolkit
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
        goto dev_menu
	)
:: -----------------------------------------------------------------------------
:relative_crop
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening dev_tools.button_extract...
	call %PYTHON% -m dev_tools.relative_crop
	pause > NUL
	goto dev_menu
	) else (
		echo :: it was not possible to open dev_tools.relative_crop, make sure you have a folder toolkit
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
        goto dev_menu
	)
:: -----------------------------------------------------------------------------
:map_extractor
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening dev_tools.button_extract...
	call %PYTHON% -m dev_tools.map_extractor
	pause > NUL
	goto dev_menu
	) else (
		echo :: it was not possible to open dev_tools.map_extractor, make sure you have a folder toolkit
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
        goto dev_menu
	)
:: -----------------------------------------------------------------------------
:word_template_extractor
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening dev_tools.button_extract...
	call %PYTHON% -m dev_tools.word_template_extractor
	pause > NUL
	goto dev_menu
	) else (
		echo :: it was not possible to open dev_tools.word_template_extractor, make sure you have a folder toolkit
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
        goto dev_menu
	)
:: -----------------------------------------------------------------------------
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
call %ADB% -s %ADB_PORT% shell mkdir /sdcard/dcim/Screenshot 2>nul
call %ADB% -s %ADB_PORT% shell screencap -p /sdcard/dcim/Screenshot/%name%.png
call %ADB% -s %ADB_PORT% pull /sdcard/dcim/Screenshot/%name%.png %SCREENSHOT_FOLDER%\%name%.png
call %ADB% -s %ADB_PORT% shell rm /sdcard/dcim/Screenshot/%name%.png
echo.
echo The file %name%.png has been copied to ./screenshots/ directory
echo.
SET time=
if NOT ["%errorlevel%"]==["0"] (
    pause
    exit /b %errorlevel%
)
goto adbss
:: -----------------------------------------------------------------------------
:u2ss
	call %PYTHON% --version >nul
	if %errorlevel% == 0 (
	echo Python Found! Proceeding..
	echo Opening dev_tools.button_extract...
	call %PYTHON% -m dev_tools.uiautomator2_screenshot
	echo The file *.png has been copied to ./screenshots/ directory
	pause > NUL
	goto dev_menu
	) else (
		echo :: it was not possible to open dev_tools.uiautomator2_screenshot, make sure you have a folder toolkit
		echo :: inside AzurLaneAutoScript folder.
		echo.
        pause > NUL
        goto dev_menu
	)
:: -----------------------------------------------------------------------------
:adbc
rem create output file name and path from parameters and date and time
rem loop
:CLOCK
set Timestamp=%date:~0,2%-%date:~3,2%-%date:~6,4%-%time:~0,2%-%time:~3,2%-%time:~6,2%-%time:~9,2%
set SCREENCAP_FILE_NAME=%FILE_PREFIX%-%Timestamp%.png
set SCREENCAP_FILE_PATH=%SCREENSHOT_FOLDER%\%SCREENCAP_FILE_NAME%

rem calling adb shell screencap, pull and remove the previos file
call %ADB% -s %ADB_PORT% shell mkdir /sdcard/dcim/Screenshot 2>nul
call %ADB% -s %ADB_PORT% shell screencap -p /sdcard/dcim/Screenshot/%SCREENCAP_FILE_NAME%
call %ADB% -s %ADB_PORT% pull /sdcard/dcim/Screenshot/%SCREENCAP_FILE_NAME% %SCREENCAP_FILE_PATH%
call %ADB% -s %ADB_PORT% shell rm /sdcard/dcim/Screenshot/%SCREENCAP_FILE_NAME%
goto:CLOCK

:EOF
exit