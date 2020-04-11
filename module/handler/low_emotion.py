from module.base.base import ModuleBase
from module.handler.assets import LOW_EMOTION_CONFIRM, LOW_EMOTION_CANCEL


class LowEmotionHandler(ModuleBase):
    def handle_combat_low_emotion(self):
        if not self.config.IGNORE_LOW_EMOTION_WARN:
            return False

        if self.appear(LOW_EMOTION_CANCEL, offset=30)\
                and self.appear(LOW_EMOTION_CONFIRM, offset=30, interval=1):
            self.device.click(LOW_EMOTION_CONFIRM)
            return True
        else:
            return False
