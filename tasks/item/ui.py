from module.logger import logger
from module.ui.switch import Switch
from tasks.base.page import page_item
from tasks.base.ui import UI
from tasks.item.assets.assets_item_consumable_usage import SIMPLE_PROTECTIVE_GEAR
from tasks.item.assets.assets_item_ui import *
from tasks.item.keywords import KEYWORD_ITEM_TAB

SWITCH_ITEM_TAB = Switch('ItemTab', is_selector=True)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.UpgradeMaterials,
    check_button=UPGRADE_MATERIAL_CHECK,
    click_button=UPGRADE_MATERIAL_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.LightCone,
    check_button=LIGHT_CONE_CHECK,
    click_button=LIGHT_CONE_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.Relics,
    check_button=RELICS_CHECK,
    click_button=RELICS_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.OtherMaterials,
    check_button=OTHER_MATERIALS_CHECK,
    click_button=OTHER_MATERIALS_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.Consumables,
    check_button=CONSUMABLE_CHECK,
    click_button=CONSUMABLE_CLICK,
)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.Missions,
    check_button=MISSIONS_CHECK,
    click_button=MISSIONS_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.Valuables,
    check_button=VALUABLES_CHECK,
    click_button=VALUABLES_CLICK
)


class ItemUI(UI):
    def item_goto(self, state: KEYWORD_ITEM_TAB, wait_until_stable=True):
        """
        Args:
            state:
            wait_until_stable: if subsequent actions are manipulating items, or any other thing that needs to load
                inside the tab, wait_until_stable should set to True

        Returns:
            self = ItemUI('alas')
            self.device.screenshot()
            self.item_goto(KEYWORD_ITEM_TAB.Relics)
            self.item_goto(KEYWORD_ITEM_TAB.Consumables)
        """
        logger.hr('Item tab goto', level=2)
        self.ui_ensure(page_item)
        SWITCH_ITEM_TAB.set(state, main=self)
        if wait_until_stable:
            logger.info(f'Tab goto {state}, wait until loaded')
            self.wait_until_stable(SIMPLE_PROTECTIVE_GEAR)
        else:
            logger.info(f'Tab goto {state}')
