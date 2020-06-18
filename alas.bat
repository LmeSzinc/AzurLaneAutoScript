@echo off

call adb kill-server > nul 2>&1
REM Change to your emulator port
adb connect 127.0.0.1:5565

echo initializing uiautomator2
python -m uiautomator2 init

:: timout
PowerShell -Command "Start-Sleep -s 3" > nul 2>&1

goto alas

:alas
	cls
	echo.
	echo  :: Alas run
	echo. 
	echo  Choose your server
    echo.
    echo     1. EN
	echo     2. CN
	echo     3. JP
	echo. 
	echo  :: Type a 'number' and press ENTER
	echo  :: Type 'exit' to quit
	echo.
	
	set /P menu=
		if %menu%==1 GOTO en
		if %menu%==2 GOTO cn
		if %menu%==3 GOTO jp
		if %menu%==exit GOTO EOF
		
		else (
		cls
	echo.
	echo  :: Incorrect Input Entered
	echo.
	echo     Please type a 'number' or 'exit'
	echo     Press any key to retry to the menu...
	echo.
		pause > NUL
		goto alas
		)
		

:en
%~dp0python/python.exe alas_en.pyw

goto alas

:cn
%~dp0python/python.exe alas_cn.pyw

goto alas

:jp
%~dp0python/python.exe alas_jp.pyw

goto alas
