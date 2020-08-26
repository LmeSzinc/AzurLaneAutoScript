@rem
:: Used for "Alas-Deploy-Tool-V4.bat"
:: Please make sure that: only call this batch when %cd% is %root%;
:: e.g.
:: call command\ConfigAlas.bat SerialAlas 127.0.0.1:5555

@echo off
setlocal EnableDelayedExpansion
set "cfg_Alas=%root%\config\alas.ini"
set "cfg_Extra=%~2"
call :Config_Common
call :Config_%~1
call :Config_Common2
goto :eof

rem ================= FUNCTIONS =================

:Config_Common

copy %cfg_Alas% %cfg_Alas%.bak > NUL
type NUL > %cfg_Alas%
goto :eof

:Config_Common2
del /Q %cfg_Alas%.bak >NUL 2>NUL
cd ..
goto :eof

:Config_SerialAlas
for /f "delims=" %%i in (%cfg_Alas%.bak) do (
   set "cfg_Content=%%i"
   echo %%i | findstr "serial" >NUL && ( set "cfg_Content=serial = %cfg_Extra%" )
   echo !cfg_Content!>>%cfg_Alas%
)
goto :eof

:Config_AzurLanePackage
for /f "delims=" %%i in (%cfg_Alas%.bak) do (
   set "cfg_Content=%%i"
   echo %%i | findstr "package_name" >NUL && ( set "cfg_Content=package_name = %cfg_Extra%" )
   echo !cfg_Content!>>%cfg_Alas%
)
goto :eof