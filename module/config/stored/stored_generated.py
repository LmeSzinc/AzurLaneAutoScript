from module.config.stored.classes import (
    StoredActionPoint,
    StoredBase,
    StoredCoin,
    StoredCounter,
    StoredInt,
    StoredOil,
    StoredStr,
)


# This file was auto-generated, do not modify it manually. To generate:
# ``` python -m module/config/config_updater.py ```

class StoredGenerated:
    Oil = StoredOil("EventGeneral.CampaignStorage.Oil")
    Coin = StoredCoin("EventGeneral.CampaignStorage.Coin")
    Gem = StoredInt("EventGeneral.CampaignStorage.Gem")
    Pt = StoredInt("EventGeneral.CampaignStorage.Pt")
    Cube = StoredInt("Gacha.GachaStorage.Cube")
    YellowCoin = StoredInt("OpsiGeneral.OpsiStorage.YellowCoin")
    PurpleCoin = StoredInt("OpsiGeneral.OpsiStorage.PurpleCoin")
    ActionPoint = StoredActionPoint("OpsiGeneral.OpsiStorage.ActionPoint")
