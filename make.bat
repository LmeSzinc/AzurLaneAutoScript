@echo off

cls

set target=%1

if not defined target (
    set target=all
)

if %target%==clean (
    call :clean
)else if %target%==all (
    call :clean
    call :pack
)else if %target%==pack (
    call :pack
) else (
    echo Unknow target: %target%
)

exit /B 0

:clean
call :title "CLEAN"
setlocal
set RM=rmdir /S /Q
%RM% build
%RM% pack
%RM% install
endlocal
exit /B 0

:pack
call :title "PACK"
setlocal
set CMAKE=cmake
%CMAKE% -B build
%CMAKE% --build build
%CMAKE% --install build
%CMAKE% --build build --target package
endlocal
exit /B 0

:title
echo ************************************************************
echo                       %~1
echo ************************************************************
exit /B 0
