"""
This file stores server, such as 'cn', 'en'.
Use 'import module.config.server as server' to import, don't use 'from xxx import xxx'.
"""
server = 'cn'  # Setting default to cn, will avoid errors when using dev_tools

VALID_SERVER = ['cn', 'en', 'jp', 'tw']
VALID_PACKAGE = {
    'com.bilibili.azurlane': 'cn',
    'com.YoStarEN.AzurLane': 'en',
    'com.YoStarJP.AzurLane': 'jp',
    'com.hkmanjuu.azurlane.gp': 'tw',
}
VALID_CHANNEL_PACKAGE = {
    # App stores
    'com.bilibili.blhx.huawei': ('cn', '华为'),
    'com.bilibili.blhx.mi': ('cn', '小米'),
    'com.tencent.tmgp.bilibili.blhx': ('cn', '腾讯应用宝'),
    'com.bilibili.blhx.baidu': ('cn', '百度'),
    'com.bilibili.blhx.qihoo': ('cn', '360'),
    'com.bilibili.blhx.oppo': ('cn', 'oppo'),
    'com.bilibili.blhx.vivo': ('cn', 'vivo'),
    'com.bilibili.blhx.mz': ('cn', '魅族'),
    # 'com.bilibili.blhx.letv': ('cn', '乐视'),  # Not confirmed
    # 'com.bilibili.blhx.gionee': ('cn', '金立'),  # Not confirmed

    # 3rd party gaming platforms
    'com.bilibili.blhx.uc': ('cn', 'UC九游'),
    'com.bilibili.blhx.mzw': ('cn', '拇指玩'),
    'com.yiwu.blhx.yx15': ('cn', '一五游戏'),

    # Tw
    'com.hkmanjuu.azurlane.gp.mc': ('tw', 'MyCard'),
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
