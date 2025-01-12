import module.config.server as server
from module.ocr.ocr import Digit
from module.shop.assets import *
from module.ui.ui import UI

if server.server != 'jp':
    OCR_SHOP_GOLD_COINS = Digit(SHOP_GOLD_COINS, letter=(239, 239, 239), name='OCR_SHOP_GOLD_COINS')
    OCR_SHOP_GEMS = Digit(SHOP_GEMS, letter=(255, 243, 82), name='OCR_SHOP_GEMS')
else:
    OCR_SHOP_GOLD_COINS = Digit(SHOP_GOLD_COINS, letter=(201, 201, 201), name='OCR_SHOP_GOLD_COINS')
    OCR_SHOP_GEMS = Digit(SHOP_GEMS, letter=(190, 180, 82), name='OCR_SHOP_GEMS')
OCR_SHOP_MEDAL = Digit(SHOP_MEDAL, letter=(239, 239, 239), name='OCR_SHOP_MEDAL')
OCR_SHOP_MERIT = Digit(SHOP_MERIT, letter=(239, 239, 239), name='OCR_SHOP_MERIT')
OCR_SHOP_GUILD_COINS = Digit(SHOP_GUILD_COINS, letter=(255, 255, 255), name='OCR_SHOP_GUILD_COINS')
OCR_SHOP_CORE = Digit(SHOP_CORE, letter=(239, 239, 239), name='OCR_SHOP_CORE')
OCR_SHOP_VOUCHER = Digit(SHOP_VOUCHER, letter=(255, 255, 255), name='OCR_SHOP_VOUCHER')


class ShopStatus(UI):
    def status_get_gold_coins(self):
        """
        Returns:
            int:

        Pages:
            in:
        """
        amount = OCR_SHOP_GOLD_COINS.ocr(self.device.image)
        return amount

    def status_get_gems(self):
        """
        Returns:
            int:

        Pages:
            in: page_shop, medal shop
        """
        amount = OCR_SHOP_GEMS.ocr(self.device.image)
        return amount

    def status_get_medal(self):
        """
        Returns:
            int:

        Pages:
            in: page_shop, medal shop
        """
        amount = OCR_SHOP_MEDAL.ocr(self.device.image)
        return amount

    def status_get_merit(self):
        """
        Returns:
            int:

        Pages:
            in: page_shop, merit shop
        """
        amount = OCR_SHOP_MERIT.ocr(self.device.image)
        return amount

    def status_get_guild_coins(self):
        """
        Returns:
            int:

        Pages:
            in: page_shop, guild shop
        """
        amount = OCR_SHOP_GUILD_COINS.ocr(self.device.image)
        return amount

    def status_get_core(self):
        """
        Returns:
            int:

        Pages:
            in: page_shop, core shop
        """
        amount = OCR_SHOP_CORE.ocr(self.device.image)
        return amount

    def status_get_voucher(self):
        """
        Returns:
            int:

        Pages:
            in: OpSi voucher shop
        """
        amount = OCR_SHOP_VOUCHER.ocr(self.device.image)
        return amount
