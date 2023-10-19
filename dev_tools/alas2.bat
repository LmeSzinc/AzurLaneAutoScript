@echo off
rem @SETLOCAL EnableExtensions EnableDelayedExpansion
pushd "%~dp0"
set ver=2.7
title Alas Run Tool %ver%
:: -----------------------------------------------------------------------------
rem :check_Permissions
rem     echo Administrative permissions required. Detecting permissions...
rem     net session >nul 2>&1
rem     if %errorLevel% == 0 (
rem         echo Success: Administrative permissions confirmed.
rem         echo Press any to continue...
rem         pause >nul
rem         call :continue
rem     ) else (
rem         echo Failure: Current permissions inadequate.
rem     )
rem     pause >nul
:: -----------------------------------------------------------------------------
:continue
set ALAS_PATH=%~dp0
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
set CURL=%ALAS_PATH%toolkit\Git\mingw64\bin\curl.exe
set API_JSON=%ALAS_PATH%log\api_git.json
set config=%~dp0config\alas.ini
set configtemp=%~dp0config\alastemp.ini
set template=%~dp0config\template.ini
set git_log="%GIT% log --pretty=format:%%H%%n%%aI -1"
:: -----------------------------------------------------------------------------
:first_run
if exist %~dp0config\alas.ini set first_run=1
if defined first_run (
    call :is_using_git
) else (
    call :not_using_git
)
:: -----------------------------------------------------------------------------
set using_git=
if exist ".git\" set using_git=1
if defined using_git (
    call :is_using_git
) else (
    call :not_using_git
)
:: -----------------------------------------------------------------------------
:is_using_git
setlocal enabledelayedexpansion
for /f "delims=" %%a in (!config!) do (
    set line=%%a
    if "x!line:~0,15!"=="xgithub_token = " (
        set github_token=!line:~15!
        
    )
)
:: -----------------------------------------------------------------------------
:bypass_first_run
rem %CURL% -s https://api.github.com/repos/lmeszinc/AzurLaneAutoScript/git/refs/heads/master?access_token=!github_token! > %~dp0log\api_git.json
%CURL% -s https://api.github.com/repos/lmeszinc/AzurLaneAutoScript/commits/master?access_token=!github_token! > %~dp0log\api_git.json
endlocal
rem for /f "skip=5 tokens=2 delims=:," %%I IN (%API_JSON%) DO IF NOT DEFINED sha SET sha=%%I 
rem set sha=%sha:"=%
rem set sha=%sha: =%
for /f "skip=1 tokens=2 delims=:," %%I IN (%API_JSON%) DO IF NOT DEFINED sha SET sha=%%I 
set sha=%sha:"=%
set sha=%sha: =%
for /f "skip=14 tokens=3 delims=:" %%I IN (%API_JSON%) DO IF NOT DEFINED message SET message=%%I 
set message=%message:"=%
set message=%message:,=%
for /f %%i in ('git rev-parse --abbrev-ref HEAD') do set BRANCH=%%i
for /f "delims=" %%i IN ('%GIT% log -1 "--pretty=%%H"') DO set LAST_LOCAL_GIT=%%i
for /f "tokens=1,2" %%A in ('%GIT% log -1 "--format=%%h %%ct" -- .') do (
    set GIT_SHA1=%%A
    call :gmTime GIT_CTIME %%B
)
:: -----------------------------------------------------------------------------
:time_parsed
if %LAST_LOCAL_GIT% == %sha% (
    echo ----------------------------------------------------------------
    echo Remote Git hash:        %sha%
    echo Remote Git message:    %message%
    echo ----------------------------------------------------------------
    echo Local Git hash:       %LAST_LOCAL_GIT%
    echo Local commit date:    %GIT_CTIME%
    echo Local Branch:         %BRANCH%
    echo ----------------------------------------------------------------
    echo your ALAS is updated
    echo Press any to continue...
    pause > NUL
    call :adb_kill
) else (
    echo ----------------------------------------------------------------
    echo Remote Git hash:        %sha%
    echo Remote Git message:    %message%
    echo ----------------------------------------------------------------
    echo Local Git hash:       %LAST_LOCAL_GIT%
    echo Local commit date:    %GIT_CTIME%
    echo Local Branch:         %BRANCH%
    echo ----------------------------------------------------------------
    popup.exe
    choice /t 10 /c yn /d y /m "There is an update for ALAS. Download now?"
    if errorlevel 2 call :adb_kill
    if errorlevel 1 call :choose_update_mode
)
:: -----------------------------------------------------------------------------
:not_using_git
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
:: -----------------------------------------------------------------------------
set SCREENSHOT_FOLDER=%~dp0screenshots
if not exist %SCREENSHOT_FOLDER% (
    mkdir %SCREENSHOT_FOLDER%
)
:: -----------------------------------------------------------------------------
:: if config\adb_port.ini dont exist, will be created
    if not exist %ADB_P% (
    cd . > %ADB_P%
        )
:: -----------------------------------------------------------------------------
:prompt
REM if adb_port is empty, prompt HOST:PORT
set adb_empty=%~dp0config\adb_port.ini
for %%A in (%adb_empty%) do if %%~zA==0 (
    echo Enter your HOST:PORT eg: 127.0.0.1:5555 for default bluestacks
    echo If you misstype, you can edit the file in config/adb_port.ini
    set /p adb_input=
    )
:: -----------------------------------------------------------------------------
REM if adb_input = 0 load from adb_port.ini
:adb_input
if [%adb_input%]==[] (
    call :CHECK_BST_BETA
    ) else (
    REM write adb_input on adb_port.ini
    echo %adb_input% >> %ADB_P%
    call :FINDSTR
)
:: -----------------------------------------------------------------------------
:: Will search for 127.0.0.1:62001 and replace for %ADB_PORT%
:FINDSTR
REM setlocal enableextensions disabledelayedexpansion
set search=127.0.0.1:62001
set replace=%adb_input%

for /f "delims=" %%i in ('type "%template%" ^& break ^> "%template%" ') do (
    set line=%%i
    setlocal enabledelayedexpansion
    >>"%template%" echo(!line:%search%=%replace%!
    endlocal
    )
)
call :CHECK_BST_BETA
:: -----------------------------------------------------------------------------
:CHECK_BST_BETA
reg query HKEY_LOCAL_MACHINE\SOFTWARE\BlueStacks_bgp64_hyperv >nul
if %errorlevel% equ 0 (
    echo ------------------------------------------------------------------------------------------
    choice /t 10 /c yn /d n /m "Bluestacks Hyper-V BETA detected, would you like to use realtime_connection mode?"
    echo ------------------------------------------------------------------------------------------
    if errorlevel 2 call :load
    if errorlevel 1 call :realtime_connection
) else (
    call :load
)
:: -----------------------------------------------------------------------------
:realtime_connection
ECHO. Connecting with realtime mode ...
for /f "tokens=3" %%a in ('reg query HKEY_LOCAL_MACHINE\SOFTWARE\BlueStacks_bgp64_hyperv\Guests\Android\Config /v BstAdbPort') do (set /a port = %%a)
set SERIAL_REALTIME=127.0.0.1:%port%
echo ----------------------------------------------------------------
echo connecting at %SERIAL_REALTIME%
call %ADB% connect %SERIAL_REALTIME%
echo ----------------------------------------------------------------
call :replace_serial
:: -----------------------------------------------------------------------------
:replace_serial
set config=%~dp0config\alas.ini
setlocal enabledelayedexpansion
for /f "delims=" %%i in (!config!) do (
    set line=%%i
    if "x!line:~0,9!"=="xserial = " (
        set serial=!line:~9!
    )
)
set search=%serial%
set replace=%SERIAL_REALTIME%
echo ----------------------------------------------------------------
echo Old Serial:      %serial%
echo New Serial:      %SERIAL_REALTIME% 
echo ----------------------------------------------------------------
echo Press any to continue...
pause > NUL
for /f "delims=" %%i in ('type "%config%" ^& break ^> "%config%" ') do (
    set line=%%i
    >>"%config%" echo(!line:%search%=%replace%!
    )
)
endlocal
call :init
:: -----------------------------------------------------------------------------
:: Deprecated
REM set /a search=104
REM set replace=serial = %SERIAL_REALTIME%
REM (for /f "tokens=1*delims=:" %%a IN ('findstr /n "^" "%config%"') do (
REM     set Line=%%b
REM     IF %%a equ %search% set Line=%replace%
REM     setlocal enabledelayedexpansion
REM     ECHO(!Line!
REM     endlocal
REM ))> %~dp0config\alastemp.ini
REM pause
REM del %config%
REM MOVE %configtemp% %config%
REM )
:: -----------------------------------------------------------------------------
:load
if defined first_run (
    call :load_alas
) else (
    call :load_input_serial
)
:: -----------------------------------------------------------------------------
:load_alas
set config=%~dp0config\alas.ini
setlocal enabledelayedexpansion
for /f "delims=" %%i in (!config!) do (
    set line=%%i
    if "x!line:~0,9!"=="xserial = " (
        set serial=!line:~9!
    )
)
call :load_alas_serial
:: -----------------------------------------------------------------------------
:load_input_serial
echo ----------------------------------------------------------------
echo connecting at %adb_input%
call %ADB% connect %adb_input%
echo ----------------------------------------------------------------
call :init
:: -----------------------------------------------------------------------------
:load_alas_serial
echo ----------------------------------------------------------------
echo connecting at !serial!
call !ADB! connect !serial!
echo ----------------------------------------------------------------
call :init
:: -----------------------------------------------------------------------------
endlocal
:: -----------------------------------------------------------------------------
:: Deprecated
REM Load adb_port.ini
REM
REM set /p ADB_PORT=<%ADB_P%
REM echo connecting at %ADB_PORT%
REM call %ADB% connect %ADB_PORT%
:: -----------------------------------------------------------------------------
:init
echo ----------------------------------------------------------------
echo initializing uiautomator2
call %PYTHON% -m uiautomator2 init
echo ----------------------------------------------------------------
echo Press any to continue...
pause > NUL
:: uncomment the pause to catch errors
REM pause
call :alas
:: -----------------------------------------------------------------------------

:alas
    cls
    echo.
    echo  :: Alas run
    echo.
    echo  Choose your option
    echo.
    echo    1. EN
    echo    2. CN
    echo    3. JP
    echo    4. UPDATER
    echo.
    echo  :: Type a 'number' and press ENTER
    echo  :: Type 'exit' to quit
    echo.
    set /P menu= || Set menu=Nothing
        if %menu%==1 call :en
        if %menu%==2 call :cn
        if %menu%==3 call :jp
        if %menu%==4 call :choose_update_mode
        if %menu%==exit call :EOF
        if %menu%==Nothing call :alas
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
    echo ----------------------------------------------------------------
    echo Python Found in %PYTHON% Proceeding..
    echo Opening alas_en.pyw in %ALAS_PATH%
    call %PYTHON% alas_en.pyw
    pause > NUL
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
    echo ----------------------------------------------------------------
    echo Python Found in %PYTHON% Proceeding..
    echo Opening alas_en.pyw in %ALAS_PATH%
    call %PYTHON% alas_cn.pyw
    pause > NUL
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
    echo ----------------------------------------------------------------
    echo Python Found in %PYTHON% Proceeding..
    echo Opening alas_en.pyw in %ALAS_PATH%
    call %PYTHON% alas_jp.pyw
    pause > NUL
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
    echo    :: This update only will work if you downloaded ALAS on
    echo    :: Release tab and installed with Easy_Install-v2.bat
    echo.
    echo    ::Overwrite local changes::
    echo.
    echo.
    echo    1) https://github.com/LmeSzinc/AzurLaneAutoScript (Main Repo, When in doubt, use it)
    echo    2) https://github.com/whoamikyo/AzurLaneAutoScript (Mirrored Fork)
    echo    3) https://github.com/whoamikyo/AzurLaneAutoScript (nightly build, dont use)
    echo    4) https://gitee.com/lmeszinc/AzurLaneAutoScript.git (Recommended for CN users)
    echo    5) https://github.com/LmeSzinc/AzurLaneAutoScript (Dev build, use only if you know what you are doing)
    echo    6) Toolkit tools updater
    echo    7) Back to main menu
    echo.
    echo    :: Type a 'number' and press ENTER
    echo    :: Type 'exit' to quit
    echo.
    set /P choice=
        if %choice%==1 call :LmeSzinc
        if %choice%==2 call :whoamikyo
        if %choice%==3 call :nightly
        if %choice%==4 call :gitee
        if %choice%==5 call :LmeSzincD
        if %choice%==6 call :toolkit_updater
        if %choice%==7 call :alas
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
    echo    :: This update only will work if you downloaded ALAS on
    echo    :: Release tab and installed with Easy_Install-v2.bat
    echo.
    echo    ::Keep local changes::
    echo.
    echo.
    echo    1) https://github.com/LmeSzinc/AzurLaneAutoScript (Main Repo, When in doubt, use it)
    echo    2) https://github.com/whoamikyo/AzurLaneAutoScript (Mirrored Fork)
    echo    3) https://github.com/whoamikyo/AzurLaneAutoScript (nightly build, dont use)
    echo    4) https://gitee.com/lmeszinc/AzurLaneAutoScript.git (Recommended for CN users)
    echo    5) Back to main menu
    echo.
    echo    :: Type a 'number' and press ENTER
    echo    :: Type 'exit' to quit
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
:LmeSzincD
    call %GIT% --version >nul
    if %errorlevel% == 0 (
    echo GIT Found in %GIT% Proceeding
    echo Updating from LmeSzinc Dev branch..
    call %GIT% fetch origin dev
    call %GIT% reset --hard origin/dev
    call %GIT% pull --ff-only origin dev
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
rem     echo.
rem     echo  :: Checking For Internet Connection to Github...
rem     echo.
rem     timeout /t 2 /nobreak > NUL

rem     ping -n 1 google.com -w 20000 >nul

rem     if %errorlevel% == 0 (
rem     echo You have a good connection with Github! Proceeding...
rem     echo press any to proceed
rem     pause > NUL
rem     call updater_menu
rem     ) else (
rem         echo  :: You don't have a good connection out of China
rem         echo  :: It might be better to update using Gitee
rem         echo  :: Redirecting...
rem         echo.
rem         echo     Press any key to continue...
rem         pause > NUL
rem         call start_gitee
rem     )
:: -----------------------------------------------------------------------------
rem Keep local changes
:: -----------------------------------------------------------------------------
:choose_update_mode
    cls
    echo.
    echo.
    echo    ::Choose update method::
    echo.
    echo    1) Overwrite local changes (Will undo any local changes)
    echo    2) Keep local changes (Useful if you have customized a map)
    echo    3) Back to main menu
    echo.
    echo    :: Type a 'number' and press ENTER
    echo    :: Type 'exit' to quit
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
    echo    :: This will add the toolkit repository for updating
    echo.
    echo    ::Toolkit::
    echo.
    echo.
    echo    1) https://github.com/whoamikyo/alas-env.git (Default Github)
    echo    2) https://gitee.com/lmeszinc/alas-env.git (Recommended for CN users)
    echo    3) Back to main menu
    echo.
    echo    :: Type a 'number' and press ENTER
    echo    :: Type 'exit' to quit
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
        echo    :: Git not found, maybe there was an installation issue
        echo    :: check if you have this directory %GIT%
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
        echo    :: Git not found, maybe there was an installation issue
        echo    :: check if you have this directory %GIT%
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
call :time_parsed
:: -----------------------------------------------------------------------------
rem :git_update_checker
rem %CURL% -s https://api.github.com/repos/lmeszinc/AzurLaneAutoScript/git/refs/heads/master?access_token=%github_token% > %~dp0log\API_GIT.json
rem FOR /f "skip=5 tokens=2 delims=:," %%I IN (%API_JSON%) DO IF NOT DEFINED sha SET sha=%%I
rem set sha=%sha:"=%
rem set sha=%sha: =%
rem FOR /F "delims=" %%i IN ('%GIT% log -1 "--pretty=%%H"') DO set LAST_LOCAL_GIT=%%i
:: -----------------------------------------------------------------------------
:: -----------------------------------------------------------------------------
rem if %LAST_LOCAL_GIT% equ %sha% SET run_update=1
rem call :alas

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
rem      REG add "HKLM\SYSTEM\CurrentControlset\Control\Session Manager\Environment" /f /v PATH /t REG_SZ /d "%PATH%;%~1" >> add-paths-detail.log
rem     IF ERRORLEVEL 0 (
rem         ECHO Adding   %1 . . . Success! >> add-paths.log
rem         set "PATH=%PATH%;%~1"
rem         rem set UPDATE=1
rem     ) ELSE (
rem         ECHO Adding   %1 . . . FAILED. Run this script with administrator privileges. >> add-paths.log
rem     )
rem ) ELSE (
rem     ECHO Skipping %1 - Already in PATH >> add-paths.log
rem     )
:: -----------------------------------------------------------------------------
rem :AddPath <pathToAdd>
rem ECHO %PATH% | FINDSTR /C:"%~1" > nul
rem IF ERRORLEVEL 1 (
rem     REG add "HKLM\SYSTEM\CurrentControlset\Control\Session Manager\Environment" /f /v PATH /t REG_SZ /d "%PATH%;%~1"  > nul 2>&1
rem     IF ERRORLEVEL 0 (
rem         ECHO Adding   %1 . . . Success!
rem         set "PATH=%PATH%;%~1"
rem         set UPDATE=1
rem     ) ELSE (
rem         ECHO Adding   %1 . . . FAILED. Run this script with administrator privileges.
rem     )
rem ) ELSE (
rem     ECHO Skipping %1 - Already in PATH
rem     )
:: -----------------------------------------------------------------------------
:EOF
echo Exiting
pause
exit
