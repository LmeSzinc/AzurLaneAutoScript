GAME_PACKAGE = {
    'com.bilibili.azurlane': 'cn',
    'com.YoStarEN.AzurLane': 'en',
    'com.YoStarJP.AzurLane': 'jp',
    'com.hkmanjuu.azurlane.gp': 'tw',
}


def package_to_server(package: str) -> str:
    return GAME_PACKAGE.get(package, 'cn')
