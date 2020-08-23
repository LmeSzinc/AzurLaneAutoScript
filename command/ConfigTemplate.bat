@rem
:: Used for "ADT-V4.bat"
:: Please make sure that: only call this batch when %cd% is %root%;
:: e.g.
:: call command\ConfigAlas.bat SerialTemplate 127.0.0.1:5555

@echo off
setlocal EnableDelayedExpansion
set "cfg_Template=%root%\config\template.ini"
set "cfg_Extra=%~2"
call :Config_Common
call :Config_%~1
call :Config_Common2
goto :eof

rem ================= FUNCTIONS =================

:Config_Common

copy %cfg_Template% %cfg_Template%.bak > NUL
type NUL > %cfg_Template%
goto :eof

:Config_Common2
del /Q %cfg_Template%.bak >NUL 2>NUL
cd ..
goto :eof

:Config_SerialTemplate
for /f "delims=" %%i in (%cfg_Template%.bak) do (
   set "cfg_Content=%%i"
   echo %%i | findstr "serial" >NUL && ( set "cfg_Content=serial = %cfg_Extra%" )
   echo !cfg_Content!>>%cfg_Template%
)
goto :eof