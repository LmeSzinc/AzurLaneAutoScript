@rem
:: Used for "Alas-Deploy-Tool-V4.bat" and Alas.bat
:: Please make sure that: only call this batch when %cd% is "toolkit\".
:: e.g.
:: call command\CheckUpdate.bat Alas
:: call command\CheckUpdate.bat AlasGitee

@echo off
call :UpdateChecker_%~1
goto :eof

rem ================= FUNCTIONS =================

:UpdateChecker_IsNotUsingGit
set /p localVersion=<command\CurrentVersion
del /Q command\RemoteVersion >NUL 2>NUL
wget %WgetOptions% %Remoterepo%/modules/CurrentVersion -O command\RemoteVersion
set /p latestVersion=<command\RemoteVersion
if "%localVersion%"=="%latestVersion%" ( set "isLatestVersion=1" ) else ( set "isLatestVersion=0" )
goto :eof

rem ================= End of File =================
