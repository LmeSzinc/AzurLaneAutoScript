@echo off
:: Initial message
echo ====================================================
echo            Easy install for ALAS
echo Install Python 3.7.6 x64, ADB, GIT, CHOCOLATEY
echo ====================================================
echo ....................................................
echo                By whoamikyo
echo ====================================================
::
echo.
:: request admin previleges, if no admin previleges
net session >nul 2>&1
if NOT %errorLevel% == 0 (
powershell start -verb runas '%0' am_admin & exit /b
)

set PATH=%PATH%;C:\Python37\;C:\Python37\Scripts\;%PROGRAMDATA%\chocolatey\lib\adb\tools\platform-tools\;%PROGRAMFILES%\Git\cmd;%PROGRAMDATA%\chocolatey\bin

:: timout
PowerShell -Command "Start-Sleep -s 10" > nul 2>&1

echo.
echo Starting Installation

:: Installing chocolatey
echo Downloading chocolatey
PowerShell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))"
call refreshenv
:: Using Environment variables for program files
:: Uninstalling/removing the platform tools older version, if they exists and  killing instances of adb if they are running
echo Uninstalling older version
adb kill-server > nul 2>&1
rmdir /Q /S "%PROGRAMFILES%\platform-tools" > nul 2>&1

echo installing ADB
choco install adb --force -y
:: timout
PowerShell -Command "Start-Sleep -s 10" > nul 2>&1
echo installing python
choco install python --version=3.7.6 -dfvym
call refreshenv
call python --version
:: timout
PowerShell -Command "Start-Sleep -s 10" > nul 2>&1
echo installing git
choco install git --force -y
call refreshenv
:: timout
PowerShell -Command "Start-Sleep -s 10" > nul 2>&1
echo Cloning repository
pushd %~dp0
git clone https://github.com/LmeSzinc/AzurLaneAutoScript.git
popd
:: timout
PowerShell -Command "Start-Sleep -s 10" > nul 2>&1

:: killing adb server
"%PROGRAMDATA%\chocolatey\lib\adb\tools\platform-tools\adb.exe" kill-server > nul 2>&1

pushd %~dp0
echo creating Virtual Environment
:: timout
PowerShell -Command "Start-Sleep -s 10" > nul 2>&1
call python -m venv .\AzurLaneAutoScript\venvalas
echo activating Virtual Environment
:: timout
PowerShell -Command "Start-Sleep -s 10" > nul 2>&1
call .\AzurLaneAutoScript\venvalas\Scripts\activate
echo installing requirements
pip install -r .\AzurLaneAutoScript\requirements.txt
popd


:: Installation done
echo.
echo.
echo Hurray!! Installation Complete, Now you can proceed
PowerShell -Command "Start-Sleep -s 10" > nul 2>&1
echo.
echo press any key to exit
pause > NUL