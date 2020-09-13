@rem
:: Used for "Alas-Deploy-Tool-V4.bat" in ==Preparation==
:: No %cd% limit.
:: e.g.
:: call command\LanguageSet.bat
:: Get system language -> %Language%

:: By default, set language to "en" and Region to "origin"
rem set "Language=en" && set "Region=origin"
:: Then enumerate all the existing translations.
rem chcp | find "65001" >NUL && set "Language=en" && set "Region=origin"
rem chcp | find "850" >NUL && set "Language=en" && set "Region=origin"
chcp | find "936" >NUL && set "Language=zh" && set "Region=cn" || set "Language=en" && set "Region=origin"
chcp | find "950" >NUL && set "Language=cht" && set "Region=cn" || set "Language=en" && set "Region=origin"
:: ... etc.
goto :eof

REM chcp 65001

:: chcp | find "936" >NUL && set "Language=zh" || set "Language=en"
