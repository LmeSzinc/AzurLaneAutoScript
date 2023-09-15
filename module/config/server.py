"""
This file stores server, such as 'cn', 'en'.
Use 'import module.config.server as server' to import, don't use 'from xxx import xxx'.
"""
lang = 'cn'  # Setting default to cn, will avoid errors when using dev_tools
server = 'CN-Official'

VALID_LANG = ['cn', 'en']
VALID_SERVER = {
    'CN-Official': 'com.miHoYo.hkrpg',
    'CN-Bilibili': 'com.miHoYo.hkrpg.bilibili',
    'OVERSEA-America': 'com.HoYoverse.hkrpgoversea',
    'OVERSEA-Asia': 'com.HoYoverse.hkrpgoversea',
    'OVERSEA-Europe': 'com.HoYoverse.hkrpgoversea',
    'OVERSEA-TWHKMO': 'com.HoYoverse.hkrpgoversea',
}
VALID_PACKAGE = set(list(VALID_SERVER.values()))


def set_lang(lang_: str):
    """
    Change language and this will affect globally,
    including assets and language specific methods.

    Args:
        lang_: package name or server.
    """
    global lang
    lang = lang_

    from module.base.resource import release_resources
    release_resources()


def to_server(package_or_server: str) -> str:
    """
    Convert package/server to server.
    To unknown packages, consider they are a CN channel servers.
    """
    # Can't distinguish different regions of oversea servers,
    # assume it's 'OVERSEA-Asia'
    if package_or_server == 'com.HoYoverse.hkrpgoversea':
        return 'OVERSEA-Asia'

    for key, value in VALID_SERVER.items():
        if value == package_or_server:
            return key
        if key == package_or_server:
            return key

    raise ValueError(f'Package invalid: {package_or_server}')


def to_package(package_or_server: str) -> str:
    """
    Convert package/server to package.
    """
    for key, value in VALID_SERVER.items():
        if value == package_or_server:
            return value
        if key == package_or_server:
            return value

    raise ValueError(f'Server invalid: {package_or_server}')
