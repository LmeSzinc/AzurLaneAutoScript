from functools import wraps

import module.equipment.assets as equip_assets
from module.logger import logger

g_equip_assets_ver = "new"


def equip_override_to_new():
    global g_equip_assets_ver
    if g_equip_assets_ver == "new":
        return

    logger.info("switch equipment assets to new version")
    equip_assets.EQUIP_1 = equip_assets.EQUIP_1_NEW
    equip_assets.EQUIP_2 = equip_assets.EQUIP_2_NEW
    equip_assets.EQUIP_3 = equip_assets.EQUIP_3_NEW
    equip_assets.FLEET_DETAIL_CHECK = equip_assets.FLEET_DETAIL_CHECK_NEW
    equip_assets.FLEET_ENTER_FLAGSHIP = equip_assets.FLEET_ENTER_FLAGSHIP_NEW


def equip_override_to_old():
    global g_equip_assets_ver
    if g_equip_assets_ver == "old":
        return

    logger.info("switch equipment assets to old version")
    equip_assets.EQUIP_1 = equip_assets.EQUIP_1_OLD
    equip_assets.EQUIP_2 = equip_assets.EQUIP_2_OLD
    equip_assets.EQUIP_3 = equip_assets.EQUIP_3_OLD
    equip_assets.FLEET_DETAIL_CHECK = equip_assets.FLEET_DETAIL_CHECK_OLD
    equip_assets.FLEET_ENTER_FLAGSHIP = equip_assets.FLEET_ENTER_FLAGSHIP_OLD


def equip_assets_override(ver: str = "old"):
    """
        Args:
            ver (str): "old" or "new"
    """

    def deco(func):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            # switch to target ver
            if ver == "old":
                equip_override_to_old()
            elif ver == "new":
                equip_override_to_new()
            else:
                raise TypeError(f"Unknown equipment assets ver: {ver}")
            res = func(*args, **kwargs)
            # switch back
            if ver == "old":
                equip_override_to_new()
            elif ver == "new":
                equip_override_to_old()
            else:
                raise TypeError(f"Unknown equipment assets ver: {ver}")
            return res

        return wrapped_function

    return deco
