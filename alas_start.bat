@echo off
if not "%2"=="snow" mshta vbscript:createobject("wscript.shell").run("""%~F0"" wind snow",vbhide)(window.close)&&exit
for /f "tokens=5" %%a in ('netstat /ano ^| findstr 22267') do taskkill /F /pid %%a
conda activate alas && python gui.py
exit
