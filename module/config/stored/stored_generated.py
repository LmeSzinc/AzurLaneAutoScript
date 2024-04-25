from module.config.stored.classes import (
    StoredBase,
    StoredCoin,
    StoredCounter,
    StoredInt,
    StoredOil,
)


# This file was auto-generated, do not modify it manually. To generate:
# ``` python -m module/config/config_updater.py ```

class StoredGenerated:
    Pt = StoredInt("EventGeneral.EventStorage.Pt")
    Oil = StoredOil("Commission.ItemStorage.Oil")
    Coin = StoredCoin("Commission.ItemStorage.Coin")
    Gem = StoredInt("Commission.ItemStorage.Gem")
    Cube = StoredInt("Commission.ItemStorage.Cube")
    Merit = StoredInt("ShopOnce.ShopStorage.Merit")
    Core = StoredInt("ShopOnce.ShopStorage.Core")
    Medal = StoredInt("ShopOnce.ShopStorage.Medal")
    GuildCoin = StoredInt("ShopOnce.ShopStorage.GuildCoin")
    YellowCoin = StoredInt("OpsiGeneral.OpsiStorage.YellowCoin")
    PurpleCoin = StoredInt("OpsiGeneral.OpsiStorage.PurpleCoin")
    ActionPoint = StoredInt("OpsiGeneral.OpsiStorage.ActionPoint")
