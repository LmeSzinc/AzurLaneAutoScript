@rem
:: Used for "ADT-V4.bat" in :InitLog
:: Please make sure that: only call this batch when %cd% is "toolkit\".
:: e.g.
:: call command\Log.bat Init New

@echo off
setlocal EnableDelayedExpansion
set "deploy_log_file=deploy.log"
set "log_Type=%~1"
set "log_DeployMode=%~2"
call :Log_%log_Type%-%log_DeployMode%
goto :eof

rem ================= Log Modes =================

:Log_Init-New
call :Log_init
call :GetPackagesInfo
( echo pipVer: %log_pipVer%
echo adbutilsVer: %log_adbutilsVer%
echo numpy: %log_numpyVer%
echo scipy: %log_scipyVer%
echo pillow: %log_pillowVer%
echo opencv-python: %log_opencv-pythonVer%
echo scikit-image: %log_scikit-imageVer%
echo lz4: %log_lz4Ver%
echo tqdm: %log_tqdmVer%
echo requests: %log_requestsVer%
echo uiautomator2: %log_uiautomator2Ver%
echo retrying: %log_retryingVer%
echo mxnet: %log_mxnetVer%
echo cnocr: %log_cnocrVer%
echo gooey: %log_gooeyVer%
echo colored: %log_coloredVer%
echo Python Levenshtein: %log_LevenshteinVer%
echo pyocr: %log_pyocrVer%) >> %deploy_log_file%
call :Log_common
goto :eof

:Log_Init-Legacy
call :Log_init
call :GetPackagesInfo
( echo pipVer: %log_pipVer%
echo adbutilsVer: %log_adbutilsVer%
echo numpy: %log_numpyVer%
echo scipy: %log_scipyVer%
echo pillow: %log_pillowVer%
echo opencv-python: %log_opencv-pythonVer%
echo scikit-image: %log_scikit-imageVer%
echo lz4: %log_lz4Ver%
echo tqdm: %log_tqdmVer%
echo requests: %log_requestsVer%
echo uiautomator2: %log_uiautomator2Ver%
echo retrying: %log_retryingVer%
echo mxnet: %log_mxnetVer%
echo cnocr: %log_cnocrVer%
echo gooey: %log_gooeyVer%
echo colored: %log_coloredVer%
echo pyocr: %log_pyocrVer%) >> %deploy_log_file%
call :Log_common
goto :eof

rem ================= FUNCTIONS =================

:GetDateTime
for /f %%a in ('WMIC OS GET LocalDateTime ^| find "."') do ( set "LDT=%%a" )
set "formattedDateTime=%LDT:~0,4%-%LDT:~4,2%-%LDT:~6,2% %LDT:~8,2%:%LDT:~10,2%:%LDT:~12,2%"
goto :eof

:GetPackagesInfo
pushd "%pyPath%\Lib\site-packages"
for /f "tokens=2 delims=-" %%i in ('dir /b "pip*.dist-info"') do ( set "log_pipVer=%%i" )
set "log_pipVer=%log_pipVer:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "adbutils*.dist-info"') do ( set "log_adbutilsVer=%%i" )
set "log_adbutilsVer=%log_adbutilsVer:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "pyocr*.dist-info"') do ( set "log_pyocrVer=%%i" )
set "log_pyocrVer=%log_pyocrVer:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "numpy*.dist-info"') do ( set "log_numpyVer=%%i" )
set "log_numpyVer=%log_numpyVer:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "scipy*.dist-info"') do ( set "log_scipyVer=%%i" )
set "log_scipyVer=%log_scipyVer:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "pillow*.dist-info"') do ( set "log_pillowVer=%%i" )
set "log_pillowVer=%log_pillowVer:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "opencv_python*.dist-info"') do ( set "log_opencv-pythonVer=%%i" )
set "log_opencv-pythonVer=%log_opencv-pythonVer:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "scikit_image*.dist-info"') do ( set "log_scikit-imageVer=%%i" )
set "log_scikit-imageVer=%log_scikit-imageVer:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "lz4*.dist-info"') do ( set "log_lz4Ver=%%i" )
set "log_lz4Ver=%log_lz4Ver:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "tqdm*.dist-info"') do ( set "log_tqdmVer=%%i" )
set "log_tqdmVer=%log_tqdmVer:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "cnocr*.dist-info"') do ( set "log_cnocrVer=%%i" )
set "log_cnocrVer=%log_cnocrVer:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "gooey*.dist-info"') do ( set "log_gooeyVer=%%i" )
set "log_gooeyVer=%log_gooeyVer:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "mxnet*.dist-info"') do ( set "log_mxnetVer=%%i" )
set "log_mxnetVer=%log_mxnetVer:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "retrying*.dist-info"') do ( set "log_retryingVer=%%i" )
set "log_retryingVer=%log_retryingVer:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "uiautomator2*.dist-info"') do ( set "log_uiautomator2Ver=%%i" )
set "log_uiautomator2Ver=%log_uiautomator2Ver:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "requests*.dist-info"') do ( set "log_requestsVer=%%i" )
set "log_requestsVer=%log_requestsVer:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "colored*.dist-info"') do ( set "log_coloredVer=%%i" )
set "log_coloredVer=%log_coloredVer:.dist=%"
for /f "tokens=2 delims=-" %%i in ('dir /b "python_Levenshtein*.dist-info"') do ( set "log_LevenshteinVer=%%i" )
set "log_LevenshteinVer=%log_LevenshteinVer:.dist=%"
popd
goto :eof

:Log_init
( echo Initialized: true
echo DeployMode: %log_DeployMode%
echo.) > %deploy_log_file%
call :Log_time
goto :eof

:Log_time
( echo ----- %log_Type% -----
echo.) >> %deploy_log_file%
call :GetDateTime
echo time: %formattedDateTime%>> %deploy_log_file%
:: echo time: %date:~0,10% %time:~0,8%>> %deploy_log_file%
echo.>> %deploy_log_file%
goto :eof

:Log_common
( echo.
echo errorlevel: !errorlevel!
echo.
echo ----- SystemInfo -----
systeminfo
echo.) >> %deploy_log_file%
goto :eof

rem ================= End of File =================
