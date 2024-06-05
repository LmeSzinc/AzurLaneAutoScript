from module.base.button import ButtonGrid
from module.base.utils import *
from module.handler.assets import AUTO_SEARCH_MENU_EXIT
from module.statistics.assets import CAMPAIGN_BONUS
from module.statistics.get_items import ITEM_GROUP, GetItemsStatistics
from module.statistics.item import Item
from module.statistics.utils import *


class BonusItem(Item):
    def predict_valid(self):
        return np.mean(rgb2gray(self.image) > 160) > 0.1


class CampaignBonusStatistics(GetItemsStatistics):
    def appear_on(self, image):
        if AUTO_SEARCH_MENU_EXIT.match(image, offset=(200, 20)) \
                and CAMPAIGN_BONUS.match(image, offset=(20, 500)):
            return True

        return False

    def _stats_get_items_load(self, image):
        ITEM_GROUP.item_class = BonusItem
        ITEM_GROUP.similarity = 0.85
        ITEM_GROUP.amount_area = (35, 51, 63, 63)
        origin = area_offset(CAMPAIGN_BONUS.button, offset=(-7, 34))[:2]
        grids = ButtonGrid(origin=origin, button_shape=(64, 64), grid_shape=(7, 2), delta=(72 + 2 / 3, 75))

        reward_bottom = AUTO_SEARCH_MENU_EXIT.button[1]
        grids.buttons = [button for button in grids.buttons if button.area[3] < reward_bottom]
        ITEM_GROUP.grids = grids

    def stats_get_items(self, image, **kwargs):
        """
        Args:
            image (np.ndarray):

        Returns:
            list[Item]:
        """
        result = super().stats_get_items(image, **kwargs)
        valid = False
        for item in result:
            if item.name == 'Coin':
                valid = True
        if valid:
            return [self.revise_item(item) for item in result]
        else:
            raise ImageError('Campaign bonus image does not have coins, dropped')

    def revise_item(self, item):
        """
        Args:
            item (Item):

        Returns:
            Item:
        """
        # Campaign bonus drop 9 to 30+ chips, but sometimes 10 is detected as 1.
        if item.name == 'Chip' and 0 < item.amount < 4:
            item.amount *= 10

        return item
