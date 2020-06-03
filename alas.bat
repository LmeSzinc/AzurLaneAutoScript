@echo off

adb connect 127.0.0.1:5555
python -m uiautomator2 init
Py alas_en.pyw