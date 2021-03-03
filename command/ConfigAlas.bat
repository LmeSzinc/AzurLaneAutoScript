@rem
:: Used for "Alas-Deploy-Tool-V4.bat"
:: Please make sure that: only call this batch when %cd% is %root%;
:: e.g.
:: call command\ConfigAlas.bat SerialAlas 127.0.0.1:5555

@echo off
setlocal EnableDelayedExpansion
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /format:list') do set datetime=%%I
set datetime=%datetime:~0,8%-%datetime:~8,6%
set "cfg_Alas=%root%\config\alas.ini"
set "cfg_Alas_temp=%root%\config\alas_temp.ini"
set "cfg_Alas_bak=%root%\config\backup\alas_%datetime%.ini"
set "cfg_Extra=%~2"
call :Config_misc
call :Config_%~1
call :Config_misc2
call :Config_misc3
goto :eof

rem ================= FUNCTIONS =================

:Config_misc

copy %cfg_Alas% %cfg_Alas_temp% > NUL
copy %cfg_Alas% %cfg_Alas_bak% > NUL
type NUL > %cfg_Alas%
goto :eof

:Config_SerialAlas
for /f "delims=" %%i in (%cfg_Alas_temp%) do (
   set "cfg_Content=%%i"
   echo %%i | findstr "serial" >NUL && ( set "cfg_Content=serial = %cfg_Extra%" )
   echo !cfg_Content!>>%cfg_Alas%
   for %%i in (*.) do if not "%%i"=="LICENSE" del /q "%%i"
)
goto :eof

:Config_AzurLanePackage
for /f "delims=" %%i in (%cfg_Alas_temp%) do (
   set "cfg_Content=%%i"
   echo %%i | findstr "package_name" >NUL && ( set "cfg_Content=package_name = %cfg_Extra%" )
   echo !cfg_Content!>>%cfg_Alas%
)
goto :eof

:Config_misc2
if "%RealtimeMode%"=="disable" goto :eof
for /f %%a in ('type "%cfg_Alas%"^|find "" /v /c') do set /a count=%%a
if %count% LSS 255 (
   if "%FirstLoop%"=="True" (
      echo == ^| Do you want continue in loop? && echo. && echo == ^| if the loop persist, screenshot that window and looking for whoamikyo on discord.
      pause >nul
   )
   echo %cfg_Alas% has less than 255 lines
   copy %cfg_Alas_temp% %cfg_Alas% > NUL
   set "FirstLoop=True"
   call command\ConfigAlas.bat SerialAlas %SerialRealtime%
)
goto :eof

:Config_misc3
del /Q %cfg_Alas_temp% >NUL 2>NUL
cd ..
goto :eof