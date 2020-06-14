@echo off

echo Start batch on %CD%
call .\venvalas\scripts\activate.bat
REM Change to your emulator port
::adb connect 127.0.0.1:5565
python -m uiautomator2 init
Py alas_en.pyw

PAUSE




