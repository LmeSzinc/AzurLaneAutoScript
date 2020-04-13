from module.base.base import ModuleBase
from module.handler.assets import POPUP_CANCEL, POPUP_CONFIRM


class PopupHandler(ModuleBase):
    _popup_offset = (3, 30)

    def handle_popup_confirm(self):
        if self.appear(POPUP_CANCEL, offset=self._popup_offset) \
                and self.appear(POPUP_CONFIRM, offset=self._popup_offset, interval=2):
            self.device.click(POPUP_CONFIRM)
            return True
        else:
            return False

    def handle_popup_cancel(self):
        if self.appear(POPUP_CONFIRM, offset=self._popup_offset) \
                and self.appear(POPUP_CANCEL, offset=self._popup_offset, interval=2):
            self.device.click(POPUP_CANCEL)
            return True
        else:
            return False
