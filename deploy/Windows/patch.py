import os
import re


def patch_trust_env(file):
    """
    People use proxies, but they never realize that proxy software leaves a
    global proxy pointing to itself even when the software is not running.
    In most situations we set `session.trust_env = False` in requests, but this
    does not effect the `pip` command.

    To handle untrusted user environment for good. We patch the code file in
    requests directly. Of course, the patch only effect the python env inside
    Alas.

    Returns:
        bool: If patched.
    """
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        if re.search('self.trust_env = True', content):
            content = re.sub('self.trust_env = True', 'self.trust_env = False', content)
            with open(file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'{file} trust_env patched')
        elif re.search('self.trust_env = False', content):
            print(f'{file} trust_env already patched')
        else:
            print(f'{file} trust_env not found')
    else:
        print(f'{file} trust_env no need to patch')


def check_running_directory():
    """
    An fool-proof mechanism.
    Show error if user is running Easy Install in compressing software,
    since Alas can't install in temp directories.
    """
    file = __file__.replace(r"\\", "/").replace("\\", "/")
    # C:/Users/<user>/AppData/Local/Temp/360zip$temp/360$3/AzurLaneAutoScript
    if 'Temp/360zip' in file:
        print('请先解压Alas的压缩包，再安装Alas')
        exit(1)
    # C:/Users/<user>/AppData/Local/Temp/Rar$EXa9248.23428/AzurLaneAutoScript
    if 'Temp/Rar' in file or 'Local/Temp' in file:
        print('Please unzip ALAS installer first')
        exit(1)


def pre_checks():
    check_running_directory()

    # patch_trust_env
    patch_trust_env('./toolkit/Lib/site-packages/requests/sessions.py')
    patch_trust_env('./toolkit/Lib/site-packages/pip/_vendor/requests/sessions.py')
