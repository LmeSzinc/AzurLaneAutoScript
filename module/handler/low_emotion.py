from module.handler.popup import PopupHandler


class LowEmotionHandler(PopupHandler):
    def handle_combat_low_emotion(self):
        if not self.config.IGNORE_LOW_EMOTION_WARN:
            return False

        return self.handle_popup_confirm()
