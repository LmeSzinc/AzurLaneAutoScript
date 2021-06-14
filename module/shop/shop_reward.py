from module.shop.shop_general import GeneralShop
from module.shop.shop_guild import GuildShop
from module.shop.shop_medal import MedalShop
from module.shop.shop_merit import MeritShop


class RewardShop(GeneralShop, GuildShop, MedalShop, MeritShop):
    pass
