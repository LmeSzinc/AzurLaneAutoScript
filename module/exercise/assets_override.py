from functools import wraps

import module.exercise.assets as exer_assets

g_exer_assets_ver = "new"


def exer_override_to_new():
    global g_exer_assets_ver
    if g_exer_assets_ver == "new":
        return

    exer_assets.EQUIP_ENTER = exer_assets.EQUIP_ENTER_NEW


def exer_override_to_old():
    global g_exer_assets_ver
    if g_exer_assets_ver == "old":
        return

    exer_assets.EQUIP_ENTER = exer_assets.EQUIP_ENTER_OLD


def exer_assets_override(ver: str = "old"):
    """
        Args:
            ver (str): "old" or "new"
    """

    def deco(func):
        @wraps(func)
        def wrapped_function(*args, **kwargs):
            # switch to target ver
            if ver == "old":
                exer_override_to_old()
            elif ver == "new":
                exer_override_to_new()
            else:
                raise TypeError(f"Unknown exerment assets ver: {ver}")
            res = func(*args, **kwargs)
            # switch back
            if ver == "old":
                exer_override_to_new()
            elif ver == "new":
                exer_override_to_old()
            else:
                raise TypeError(f"Unknown exerment assets ver: {ver}")
            return res

        return wrapped_function

    return deco
