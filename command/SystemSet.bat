@rem
:: Used for "ADT-V4.bat" in ==Preparation==
:: No %cd% limit.
:: e.g.
:: call command\SystemSet.bat
:: Get system -> %SystemType% %FirstRun% %IsUsingGit%

set "AlasConfig=%root%\config\alas.ini"
set "template=%root%\config\template.ini"
set "gitFolder=%root%\.git"

:SystemSet_SystemType
if /i "%PROCESSOR_IDENTIFIER:~0,3%"=="x86" (
	set "SystemType=32"
) else (
	set "SystemType=64"
)

:: Another way
:: WMIC OS GET OSArchitecture | find "64" >NUL && set "SystemType=64" || set "SystemType=32"

:SystemSet_FirstRun
if NOT exist "%AlasConfig%" (
	set "FirstRun=yes"
) else (
	set "FirstRun=no"
)

:SystemSet_IsUsingGit

if exist "%gitFolder%" (
	set "IsUsingGit=yes"
) else (
	set "IsUsingGit=no"
)

call command\Config.bat IsUsingGit %IsUsingGit%
call command\Config.bat FirstRun %FirstRun%

rem ================= End of File =================