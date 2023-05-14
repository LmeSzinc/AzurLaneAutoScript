"""
This file stores server, such as 'cn', 'en'.
Use 'import module.config.server as server' to import, don't use 'from xxx import xxx'.
"""
server = 'cn'  # Setting default to cn, will avoid errors when using dev_tools

VALID_SERVER = ['cn', ]
VALID_PACKAGE = {
    'com.miHoYo.hkrpg': 'cn',
    'com.HoYoverse.hkrpgoversea': 'oversea'
}
VALID_CHANNEL_PACKAGE = {
    'com.miHoYo.hkrpg.bilibili': ('cn', 'Bilibili'),
}


def set_server(package_or_server: str):
    """
    Change server and this will effect globally,
    including assets and server specific methods.

    Args:
        package_or_server: package name or server.
    """
    global server
    server = to_server(package_or_server)

    from module.base.resource import release_resources
    release_resources()


def to_server(package_or_server: str) -> str:
    """
    Convert package/server to server.
    To unknown packages, consider they are a CN channel servers.
    """
    if package_or_server in VALID_SERVER:
        return package_or_server
    elif package_or_server in VALID_PACKAGE:
        return VALID_PACKAGE[package_or_server]
    elif package_or_server in VALID_CHANNEL_PACKAGE:
        return VALID_CHANNEL_PACKAGE[package_or_server][0]
    else:
        return 'cn'


def to_package(package_or_server: str) -> str:
    """
    Convert package/server to package.
    """
    package_or_server = package_or_server.lower()
    if package_or_server in VALID_PACKAGE:
        return package_or_server

    for key, value in VALID_PACKAGE.items():
        if value == package_or_server:
            return key

    raise ValueError(f'Server invalid: {package_or_server}')
