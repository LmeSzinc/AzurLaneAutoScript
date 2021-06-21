from module.build.ui import BuildUI
from module.shop.shop_general import GeneralShop
from module.shop.shop_guild import GuildShop
from module.shop.shop_medal import MedalShop
from module.shop.shop_merit import MeritShop
from module.shop.ui import ShopUI


class RewardShop(BuildUI, ShopUI, GeneralShop, GuildShop, MedalShop, MeritShop):
    pass
