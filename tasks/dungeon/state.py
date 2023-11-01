import threading

from module.base.timer import Timer
from module.base.utils import crop
from module.logger import logger
from module.ocr.ocr import DigitCounter
from tasks.base.ui import UI
from tasks.dungeon.assets.assets_dungeon_state import OCR_SIMUNI_POINT, OCR_SIMUNI_POINT_OFFSET, OCR_STAMINA


class OcrSimUniPoint(DigitCounter):
    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('O', '0').replace('o', '0')
        return result


class DungeonState(UI):
    def dungeon_get_simuni_point(self, image=None) -> int:
        """
        Page:
            in: page_guide, Survival_Index, Simulated_Universe
        """
        logger.info('Get simulated universe points')
        if image is None:
            image = self.device.image

        _ = OCR_SIMUNI_POINT_OFFSET.match_template(image)
        OCR_SIMUNI_POINT.load_offset(OCR_SIMUNI_POINT_OFFSET)
        area = (
            OCR_SIMUNI_POINT.area[0],
            OCR_SIMUNI_POINT.button[1],
            OCR_SIMUNI_POINT.area[2],
            OCR_SIMUNI_POINT.button[3],
        )

        ocr = OcrSimUniPoint(OCR_SIMUNI_POINT)
        value, _, total = ocr.ocr_single_line(crop(image, area), direct_ocr=True)
        if total and value <= total:
            logger.attr('SimulatedUniverse', f'{value}/{total}')
            self.config.stored.SimulatedUniverse.set(value, total)
            return value
        else:
            logger.warning(f'Invalid SimulatedUniverse points: {value}/{total}')
            return 0

    def dungeon_update_stamina(self, image=None, skip_first_screenshot=True):
        """
        Returns:
            bool: If success

        Pages:
            in: page_guild, Survival_Index, Simulated_Universe
                or page_rogue, LEVEL_CONFIRM
                or rogue, REWARD_CLOSE
        """
        ocr = DigitCounter(OCR_STAMINA)
        timeout = Timer(1, count=2).start()
        if image is None:
            image = self.device.image
        else:
            skip_first_screenshot = True

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            stamina = (0, 0, 0)
            immersifier = (0, 0, 0)

            if timeout.reached():
                logger.warning('dungeon_update_stamina() timeout')
                return False

            for row in ocr.detect_and_ocr(image):
                if row.ocr_text.isdigit():
                    continue
                if row.ocr_text == '+':
                    continue
                if '/' not in row.ocr_text:
                    continue
                data = ocr.format_result(row.ocr_text)
                if data[2] == self.config.stored.TrailblazePower.FIXED_TOTAL:
                    stamina = data
                if data[2] == self.config.stored.Immersifier.FIXED_TOTAL:
                    immersifier = data

            if stamina[2] > 0 and immersifier[2] > 0:
                break
            if image is not None:
                logger.warning('dungeon_update_stamina() ended')
                return

        stamina = stamina[0]
        immersifier = immersifier[0]
        logger.attr('TrailblazePower', stamina)
        logger.attr('Imersifier', immersifier)
        with self.config.multi_set():
            self.config.stored.TrailblazePower.value = stamina
            self.config.stored.Immersifier.value = immersifier
        return True

    def dungeon_update_simuni(self):
        """
        Update rogue weekly points, stamina, immersifier
        Run in a new thread to be faster as data is not used immediately

        Page:
            in: page_guide, Survival_Index, Simulated_Universe
        """
        logger.info('dungeon_update_simuni')

        def func(image):
            logger.info('Update thread start')
            with self.config.multi_set():
                self.dungeon_get_simuni_point(image)
                self.dungeon_update_stamina(image)

        thread = threading.Thread(target=func, args=(self.device.image,))
        thread.start()
