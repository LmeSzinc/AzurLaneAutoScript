from calendar import day_name

from module.base.timer import Timer
from module.campaign.campaign_status import CampaignStatus
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2
from module.config.utils import get_server_weekday
from module.freebies.assets import *
from module.logger import logger
from module.ocr.ocr import Digit
from module.shop.assets import SHOP_OCR_OIL, SHOP_OCR_OIL_CHECK
from module.ui.page import page_shop, page_supply_pack


class SupplyPack(CampaignStatus):
    def supply_pack_buy(self, supply_pack, skip_first_screenshot=True):
        """
        Args:
            supply_pack (Button): Button of supply pack, click to buy.
            skip_first_screenshot (bool):

        Returns:
            bool: If bought.
        """
        logger.hr('Supply pack buy')
        [self.interval_clear(asset) for asset in [GET_ITEMS_1, GET_ITEMS_2, supply_pack, BUY_CONFIRM]]

        logger.info(f'Buying {supply_pack}')
        executed = False
        click_count = 0
        confirm_timer = Timer(1, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(supply_pack, offset=(20, 20), interval=3):
                if click_count >= 3:
                    logger.warning(f'Failed to buy {supply_pack} after 3 trail, probably reached resource limit, skip')
                    break
                self.device.click(supply_pack)
                click_count += 1
                confirm_timer.reset()
                continue
            if self.appear_then_click(BUY_CONFIRM, offset=(20, 20), interval=3):
                confirm_timer.reset()
                continue
            if self.handle_popup_confirm('BUY_SUPPLY_PACK'):
                self.interval_reset(supply_pack)
                self.interval_reset(BUY_CONFIRM)
                executed = True
                continue
            for button in [GET_ITEMS_1, GET_ITEMS_2]:
                if self.appear_then_click(button, offset=(30, 30), interval=3):
                    confirm_timer.reset()
                    continue

            # End
            if self.appear(page_supply_pack.check_button, offset=(20, 20)) \
                    and not self.appear(supply_pack, offset=(20, 20)):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

        logger.info(f'Supply pack buy finished, executed={executed}')
        return executed

    def goto_supply_pack(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_shop
            out: page_supply_pack, supply pack tab
        """
        self.ui_goto(page_supply_pack, skip_first_screenshot=skip_first_screenshot)

    def run(self):
        """
        Pages:
            in: Any page
            out: page_supply_pack, supply pack tab
        """
        self.ui_ensure(page_shop)
        self.goto_supply_pack()
        if self.get_oil() < 21000:
            server_today = get_server_weekday()
            target = self.config.SupplyPack_DayOfWeek
            target_name = day_name[target]
            if server_today >= target:
                self.supply_pack_buy(FREE_SUPPLY_PACK)
            else:
                logger.info(f'Delaying free week supply pack to {target_name}')
        else:
            logger.info('Oil > 21000, unable to buy free weekly supply pack')


class SupplyPack_250814(SupplyPack):
    def get_oil(self, skip_first_screenshot=True):
        """
        Returns:
            int: Oil amount
        """
        amount = 0
        timeout = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Get oil timeout')
                break

            if not self.appear(SHOP_OCR_OIL_CHECK, offset=(10, 2)):
                logger.info('No oil icon')
                continue
            ocr = Digit(SHOP_OCR_OIL, name='OCR_OIL', letter=(247, 247, 247), threshold=128)
            amount = ocr.ocr(self.device.image)
            if amount >= 100:
                break

        return amount

    def goto_supply_pack(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_shop
            out: page_supply_pack, supply pack tab
        """
        logger.info('Goto supply pack')
        for _ in self.loop():

            if self.match_template_color(page_supply_pack.check_button, offset=(20, 20)):
                logger.info('At supply pack')
                break

            elif self.appear_then_click(page_supply_pack.check_button, offset=(20, 20), interval=3):
                continue
