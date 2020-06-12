@ECHO off
set PATH=%PATH%;C:\Program Files\Git\cmd
cls
:start
ECHO.
ECHO 1. https://github.com/LmeSzinc/AzurLaneAutoScript
ECHO 2. https://github.com/whoamikyo/AzurLaneAutoScript
set choice=
set /p choice=Choose the repository you want to use.
if not '%choice%'=='' set choice=%choice:~0,1%
if '%choice%'=='1' goto LmeSzinc
if '%choice%'=='2' goto whoamikyo
ECHO "%choice%" is not valid, try again
ECHO.
goto start
:LmeSzinc
git pull https://github.com/LmeSzinc/AzurLaneAutoScript.git
goto end
:whoamikyo
git pull https://github.com/whoamikyo/AzurLaneAutoScript.git
goto end
:end
pause