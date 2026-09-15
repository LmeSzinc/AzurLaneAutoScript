from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.exception import GameStuckError
from module.island.assets import *
from module.island_handler.dock import IslandDock
from module.island_handler.dock_scanner import CharacterScanner
from module.logger import logger
from module.ui.page import page_island_manage, page_island_phone

ISLAND_COLLECT_WORKSLOT_GRID = ButtonGrid(
    origin=(832, 227), delta=(95, 0), button_shape=(74, 74), grid_shape=(3, 1)
)


class IslandCollect(IslandDock):
    def collect_location_unselected_buttons(self):
        buttons = []
        if not self.is_button_selected(ISLAND_COLLECT_LOCATION_1):
            buttons.append(ISLAND_COLLECT_LOCATION_1)
        if not self.is_button_selected(ISLAND_COLLECT_LOCATION_2):
            buttons.append(ISLAND_COLLECT_LOCATION_2)
        return buttons

    def collect_available(self):
        for _ in self.loop(timeout=10):
            if self.appear_then_click(ISLAND_COLLECT_SELECT_ENTER, offset=(20, 20), interval=3):
                continue
            # End
            if self.appear(ISLAND_COLLECT_SELECT_CONFIRM, offset=(20, 20)):
                break
        else:
            logger.warning('Cannot find collect enter button, collect may not be available')
            return False

        available = None
        for _ in self.loop(skip_first=False, timeout=20):
            # End
            if self.handle_info_bar():
                logger.warning('Info bar appears, nothing more to collect')
                available = False
                break
            if self.match_template_color(ISLAND_COLLECT_START_UNAVAILABLE, offset=(20, 20)):
                logger.info('has something to collect, continue')
                available = True
                break

            if self.appear(ISLAND_COLLECT_SELECT_CONFIRM, offset=(20, 20)):
                buttons = self.collect_location_unselected_buttons()
                if not buttons:
                    self.device.click(ISLAND_COLLECT_SELECT_CONFIRM)
                    continue
                for button in buttons:
                    self.device.click(button)
                continue
        else:
            logger.warning('Cannot determine collect availability, possibly due to network issues')
            available = False

        if available:
            return True
        # Back to island manage page
        for _ in self.loop(timeout=10):
            if self.appear_then_click(ISLAND_COLLECT_SELECT_CANCEL, offset=(20, 20), interval=3):
                continue
            if self.ui_page_appear(page_island_manage, offset=(20, 20)):
                break
        else:
            logger.warning('Cannot return to island manage page, something may be wrong')
            raise GameStuckError('Cannot return to island manage page, something may be wrong')
        return False

    def collect_execute(self):
        for workslot, button in enumerate(ISLAND_COLLECT_WORKSLOT_GRID.buttons):
            click_timer = Timer(1, count=3)
            for _ in self.loop(timeout=10):
                # End
                if self.is_in_island_dock():
                    break
                if click_timer.reached():
                    self.device.click(button)
                    click_timer.reset()
            else:
                logger.warning(f'Failed to click workslot button for workslot {workslot}')
                return False
            self.island_dock_sort_method_dsc_set(enable=False)
            dock_grid = super().dock_grid
            scanner = CharacterScanner(dock_grid, emotion=(80, 150), status='free')
            scanner.disable('emotion_limit')
            candidates = scanner.scan(self.device.image)
            if not candidates:
                logger.warning(f'No candidate found for workslot {workslot}, canceling collect')
                self.island_dock_quit()
                return False
            button = candidates[0].button
            self.island_dock_select_one(button)
            self.island_dock_select_confirm(check_button=[ISLAND_COLLECT_START, ISLAND_COLLECT_START_UNAVAILABLE])
            if self.match_template_color(ISLAND_COLLECT_START, offset=(20, 20)):
                break
        if not self.match_template_color(ISLAND_COLLECT_START, offset=(20, 20)):
            logger.warning('Failed to start collect, something may be wrong')
            return False
        confirm_timer = Timer(3, count=5).start()
        for _ in self.loop(timeout=10):
            if self.handle_island_additional():
                confirm_timer.reset()
                continue
            if self.match_template_color(ISLAND_COLLECT_START, offset=(20, 20)):
                self.device.click(ISLAND_COLLECT_START)
                confirm_timer.reset()
                continue

            # End
            if self.appear(ISLAND_COLLECT_SELECT_ENTER, offset=(20, 20)):
                if confirm_timer.reached():
                    return True
        else:
            logger.warning('Failed to start collect, something may be wrong')
            return False

    def run(self):
        self.ui_ensure(page_island_manage)
        self.island_manage_side_navbar_ensure(upper=3)

        if self.collect_available():
            success = self.collect_execute()
            if success:
                logger.info('Collect successfully')
                self.config.task_delay(server_update=True)
            else:
                logger.warning('Failed to collect, will retry later')
                self.config.task_delay(success=False)
        else:
            logger.info('Collect not available, possibly due to cooldown')
            for _ in self.loop():
                if self.appear_then_click(ISLAND_COLLECT_SELECT_CANCEL, offset=(20, 20), interval=3):
                    continue
                if self.appear(ISLAND_COLLECT_SELECT_ENTER, offset=(20, 20)):
                    break
            self.config.task_delay(server_update=True)
