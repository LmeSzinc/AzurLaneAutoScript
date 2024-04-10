import time

from deploy.Windows.logger import logger

output = r"""
Process: [ 0% ]
./toolkit/Lib/site-packages/requests/sessions.py trust_env already patched
./toolkit/Lib/site-packages/pip/_vendor/requests/sessions.py trust_env already patched
./toolkit/Lib/site-packages/uiautomator2/init.py minicap_urls no need to patch
./toolkit/Lib/site-packages/uiautomator2/init.py appdir already patched
./toolkit/Lib/site-packages/adbutils/mixin.py apkutils2 no need to patch
Process: [ 5% ]
==================== SHOW DEPLOY CONFIG ====================
Repository: https://e.coding.net/llop18870/alas/AzurLaneAutoScript.git
Branch: feature
PypiMirror: https://pypi.tuna.tsinghua.edu.cn/simple
Language: zh-CN
Rest of the configs are the same as default
Process: [ 10% ]
+---------------------------------------------------+
|                    UPDATE ALAS                    |
+---------------------------------------------------+
==================== GIT INIT ====================
"D:/AlasRelease/AzurLaneAutoScript/toolkit/Git/mingw64/bin/git.exe" init
Reinitialized existing Git repository in D:/AlasRelease/AzurLaneAutoScript/.git/
[ success ]
Process: [ 15% ]
==================== SET GIT PROXY ====================
Git config http.proxy = None
Git config https.proxy = None
Git config http.sslVerify = true
Process: [ 18% ]
==================== SET GIT REPOSITORY ====================
Git config remote "origin".url = https://e.coding.net/llop18870/alas/AzurLaneAutoScript.git
Process: [ 20% ]
==================== FETCH REPOSITORY BRANCH ====================
"D:/AlasRelease/AzurLaneAutoScript/toolkit/Git/mingw64/bin/git.exe" fetch origin feature
From https://e.coding.net/llop18870/alas/AzurLaneAutoScript
 * branch              feature    -> FETCH_HEAD
[ success ]
Process: [ 40% ]
==================== PULL REPOSITORY BRANCH ====================
"D:/AlasRelease/AzurLaneAutoScript/toolkit/Git/mingw64/bin/git.exe" reset --hard origin/feature
HEAD is now at 11595208 Fix: No process cache since it's fast already
[ success ]
Process: [ 45% ]
"D:/AlasRelease/AzurLaneAutoScript/toolkit/Git/mingw64/bin/git.exe" checkout feature
Already on 'feature'
Your branch is up to date with 'origin/feature'.
[ success ]
Process: [ 48% ]
==================== SHOW VERSION ====================
"D:/AlasRelease/AzurLaneAutoScript/toolkit/Git/mingw64/bin/git.exe" --no-pager log --no-merges -1
commit 11595208afe1ca1b3d48f5722795ce2387bccd87 (HEAD -> feature, origin/feature)
Author: LmeSzinc <37934724+LmeSzinc@users.noreply.github.com>
Date:   Tue Apr 4 01:17:09 2023 +0800

    Fix: No process cache since it's fast already
[ success ]
Process: [ 50% ]
+----------------------------------------------------------+
|                    KILL EXISTING ALAS                    |
+----------------------------------------------------------+
List process
Found 264 processes
Process: [ 60% ]
+-----------------------------------------------------------+
|                    UPDATE DEPENDENCIES                    |
+-----------------------------------------------------------+
All dependencies installed
Process: [ 70% ]
+--------------------------------------------------+
|                    UPDATE APP                    |
+--------------------------------------------------+
Old file: D:\AlasRelease\AzurLaneAutoScript\toolkit\WebApp\resources\app.asar
New version: 0.3.7
New file: D:\AlasRelease\AzurLaneAutoScript\toolkit\lib\site-packages\alas_webapp\app.asar
app.asar is already up to date
Process: [ 75% ]
+---------------------------------------------------------+
|                    START ADB SERVICE                    |
+---------------------------------------------------------+
==================== REPLACE ADB ====================
No need to replace
Process: [ 90% ]
==================== ADB CONNECT ====================
-------------------- ADB DEIVCES --------------------
D:/AlasRelease/AzurLaneAutoScript/toolkit/Lib/site-packages/adbutils/binaries/adb.exe devices
DataAdbDevice(serial='127.0.0.1:16384', status='device')
DataAdbDevice(serial='127.0.0.1:16480', status='device')
DataAdbDevice(serial='127.0.0.1:7555', status='device')
Process: [ 92% ]
-------------------- BRUTE FORCE CONNECT --------------------
already connected to 127.0.0.1:7555
already connected to 127.0.0.1:16384
already connected to 127.0.0.1:16480
already connected to 127.0.0.1:7555
Process: [ 98% ]
-------------------- ADB DEIVCES --------------------
D:/AlasRelease/AzurLaneAutoScript/toolkit/Lib/site-packages/adbutils/binaries/adb.exe devices
DataAdbDevice(serial='127.0.0.1:16384', status='device')
DataAdbDevice(serial='127.0.0.1:16480', status='device')
DataAdbDevice(serial='127.0.0.1:7555', status='device')
Process: [ 100% ]
中文测试，！@#nfoir
"""


def run():
    for row in output.split('\n'):
        time.sleep(0.05)
        if row:
            logger.info(row)


if __name__ == '__main__':
    run()
