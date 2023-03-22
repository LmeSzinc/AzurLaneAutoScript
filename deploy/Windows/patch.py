import os
import re


def _patch_trust_env(file):
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


def patch_trust_env():
    _patch_trust_env('./toolkit/Lib/site-packages/requests/sessions.py')
    _patch_trust_env('./toolkit/Lib/site-packages/pip/_vendor/requests/sessions.py')
