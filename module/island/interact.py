from module.logger import logger
from module.island.assets import *
from module.ui.ui import UI
from module.base.timer import Timer
from module.base.button import Button
from module.base.template import Template

class IslandInteract(UI):
    # just a random spot to dismiss dialogs
    BTN_EMPTY = Button(area=(500, 20, 510, 30), color=(), button=(500, 20, 510, 30), name='Island Popup Dismiss')

    def goto_ui(self, target_page):
        return self.ui_goto(target_page, get_ship=False)

    def dismiss(self, repeats=1):
        """
        Dismiss any popups if exist
        """
        for _ in range(repeats):
            self.device.click(self.BTN_EMPTY)
            self.device.sleep(0.1)

    def click_and_wait_until_appear(self,
                                    btn: Button,
                                    *targets: list,
                                    threshold=20,
                                    similarity=0.85,
                                    timeout=Timer(5, 10),
                                    interval=1
                                    ):
        """
        Click a button and wait until one of given target appear

        Args:
            btn: Button to click
            targets: List of target template or button to wait for
            threshold: Matching threshold for button
            similarity: Similarity threshold for target
            timeout: Timeout timer
            interval: Interval between click and check
        Returns:
            The target button appeared, or None if timeout
        """
        timeout.reset()
        while 1:
            if timeout.reached():
                logger.error(f'Timeout waiting for {",".join([t.name for t in targets])} to appear')
                return False
            self.device.click(btn)
            self.device.sleep(interval)
            self.device.screenshot()
            for t in targets:
                if isinstance(t, Button):
                    if self.appear(t, threshold=threshold, similarity=similarity):
                        return t
                elif isinstance(t, Template):
                    sim, btn = t.match_luma_result(self.device.image)
                    if sim >= similarity:
                        return btn
                else:
                    logger.warning(f'Invalid target type: {type(t)}')
