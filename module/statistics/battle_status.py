from module.ocr.ocr import Ocr
from module.statistics.assets import ENEMY_NAME

ENEMY_NAME_OCR = Ocr(ENEMY_NAME, lang='cnocr', threshold=128)


class BattleStatusStatistics:
    def stats_battle_status(self, image):
        """
        Args:
            image: Pillow image.

        Returns:
            str: Enemy name, such as '中型主力舰队'.
        """
        result = ENEMY_NAME_OCR.ocr(image)
        # Delete wrong OCR result
        for letter in '-一个―~(':
            result = result.replace(letter, '')

        return result
