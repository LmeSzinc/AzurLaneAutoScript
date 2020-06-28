@SETLOCAL EnableExtensions EnableDelayedExpansion
@echo off
title Dev_tools
pushd %~dp0
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
:: Screenshots
SET SCREENSHOT_FOLDER=%~dp0screenshots
:: -----------------------------------------------------------------------------
set SCREENSHOT_FOLDER=%~dp0screenshots
if not exist %SCREENSHOT_FOLDER% (
  mkdir %SCREENSHOT_FOLDER%
)
rem if config\adb_port.ini dont exist, will be created
if not exist %ADB_P% (
  cd . > %ADB_P%
)
:: -----------------------------------------------------------------------------
REM if adb_port is empty, prompt HOST:PORT
SET "adb_empty=%~dp0config\adb_port.ini"
for %%A in (%adb_empty%) do if %%~zA==0 (
    echo enter your HOST:PORT eg: 127.0.0.1:5555 for default bluestacks
	echo WARNING! DONT FORGET TO SETUP AGAIN IN, ALAS ON EMULATOR SETTINGS FUNCTION
    set /p adb_input=
)
:: -----------------------------------------------------------------------------
REM if adb_input = 0 load from adb_port.ini
if [%adb_input%]==[] (
    goto load
)
REM write adb_input on adb_port.ini
echo %adb_input% >> %ADB_P%

REM Load adb_port.ini
:load
REM 
set /p ADB_PORT=<%ADB_P%

echo connecting at %ADB_PORT%
call %ADB% connect %ADB_PORT%
:: -----------------------------------------------------------------------------
:continue
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
::loop
:LOOP
FOR /f %%a IN ('WMIC OS GET LocalDateTime ^| FIND "."') DO SET DTS=%%a  
SET DATETIME=%DTS:~0,8%-%DTS:~8,6%-%DTS:~9,2%
SET SCREENCAP_FILE_NAME=screenshot-%DATETIME%.png
SET SCREENCAP_FILE_PATH=%SCREENSHOT_FOLDER%\%SCREENCAP_FILE_NAME%
::calling adb shell screencap, pull and remove the previos file
call %ADB% -s %ADB_PORT% shell mkdir /sdcard/dcim/Screenshot 2>nul
call %ADB% -s %ADB_PORT% shell screencap -p /sdcard/dcim/Screenshot/%SCREENCAP_FILE_NAME%
call %ADB% -s %ADB_PORT% pull /sdcard/dcim/Screenshot/%SCREENCAP_FILE_NAME% %SCREENCAP_FILE_PATH%
call %ADB% -s %ADB_PORT% shell rm /sdcard/dcim/Screenshot/%SCREENCAP_FILE_NAME%
goto:LOOP

:EOF
exit