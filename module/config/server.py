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
    'com.bilibili.blhx.nearme.gamecenter': ('cn', 'oppo'),
    'com.bilibili.blhx.vivo': ('cn', 'vivo'),
    'com.bilibili.blhx.mz': ('cn', '魅族'),
    'com.bilibili.blhx.dl': ('cn', '当乐'),
    'com.bilibili.blhx.lenovo': ('cn', '联想'),
    # 'com.bilibili.blhx.letv': ('cn', '乐视'),  # Not confirmed
    # 'com.bilibili.blhx.gionee': ('cn', '金立'),  # Not confirmed

    # 3rd party gaming platforms
    'com.bilibili.blhx.uc': ('cn', 'UC九游'),
    'com.bilibili.blhx.mzw': ('cn', '拇指玩'),
    'com.yiwu.blhx.yx15': ('cn', '一五游戏'),
    'com.bilibili.blhx.m4399': ('cn', '4399'),
    'com.bilibili.blhx.bilibiliMove': ('cn', '迁移'),

    # Tw
    'com.hkmanjuu.azurlane.gp.mc': ('tw', 'MyCard'),
}
DICT_PACKAGE_TO_ACTIVITY = {
    # com.manjuu.azurlane.MainActivity
    # VALID_PACKAGE
    'com.bilibili.azurlane': 'com.manjuu.azurlane.MainActivity',
    'com.YoStarEN.AzurLane': 'com.manjuu.azurlane.PrePermissionActivity',
    'com.YoStarJP.AzurLane': 'com.manjuu.azurlane.PrePermissionActivity',
    'com.hkmanjuu.azurlane.gp': 'com.manjuu.azurlane.PrePermissionActivity',
    # App stores
    'com.bilibili.blhx.huawei': 'com.manjuu.azurlane.SplashActivity',
    'com.bilibili.blhx.mi': 'com.manjuu.azurlane.SplashActivity',
    'com.tencent.tmgp.bilibili.blhx': 'com.manjuu.azurlane.SplashActivity',
    'com.bilibili.blhx.baidu': 'com.manjuu.azurlane.SplashActivity',
    'com.bilibili.blhx.qihoo': 'com.manjuu.azurlane.SplashActivity',
    'com.bilibili.blhx.nearme.gamecenter': 'com.manjuu.azurlane.SplashActivity',
    'com.bilibili.blhx.vivo': 'com.manjuu.azurlane.SplashActivity',
    'com.bilibili.blhx.mz': 'com.manjuu.azurlane.SplashActivity',
    'com.bilibili.blhx.dl': 'com.manjuu.azurlane.SplashActivity',
    'com.bilibili.blhx.lenovo': 'com.manjuu.azurlane.SplashActivity',

    # 3rd party gaming platforms
    'com.bilibili.blhx.uc': 'com.manjuu.azurlane.SplashActivity',
    'com.bilibili.blhx.mzw': 'com.manjuu.azurlane.SplashActivity',
    'com.yiwu.blhx.yx15': 'com.manjuu.azurlane.SplashActivity',
    'com.bilibili.blhx.m4399': 'com.manjuu.azurlane.SplashActivity',
    'com.bilibili.blhx.bilibiliMove': 'com.manjuu.azurlane.SplashActivity',

    # Tw
    'com.hkmanjuu.azurlane.gp.mc': 'com.manjuu.azurlane.PrePermissionActivity',
}
VALID_SERVER_LIST = {
    'cn_android': [
        '莱茵演习', '巴巴罗萨', '霸王行动', '冰山行动', '彩虹计划',
        '发电机计划', '瞭望台行动', '十字路口行动', '朱诺行动',
        '杜立特空袭', '地狱犬行动', '开罗宣言', '奥林匹克行动',
        '小王冠行动', '波茨坦公告', '白色方案', '瓦尔基里行动',
        '曼哈顿计划', '八月风暴', '秋季旅行', '水星行动', '莱茵河卫兵',
        '北极光计划', '长戟计划', '暴雨行动'
    ],
    'cn_ios': [
        '夏威夷', '珊瑚海', '中途岛', '铁底湾', '所罗门', '马里亚纳',
        '莱特湾', '硫磺岛', '冲绳岛', '阿留申群岛', '马耳他'
    ],
    'cn_channel': [
        '皇家巡游', '大西洋宪章', '十字军行动', '龙骑兵行动', '冥王星行动'
    ],
    'en': [
        'Avrora', 'Lexington', 'Sandy', 'Washington', 'Amagi',
        'Little Enterprise'
    ],
    'jp': [
        'ブレスト', '横須賀', '佐世保', '呉', '舞鶴',
        'ルルイエ', 'サモア', '大湊', 'トラック', 'ラバウル',
        '鹿児島', 'マドラス', 'サンディエゴ', '竹敷', 'キール',
        '若松', 'オデッサ', 'スイートバン'
    ]
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
